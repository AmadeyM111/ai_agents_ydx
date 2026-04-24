from __future__ import annotations

import copy
import inspect
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
except Exception:
    @dataclass
    class _BaseMessage:
        content: str = ""

    @dataclass
    class HumanMessage(_BaseMessage):
        pass

    @dataclass
    class SystemMessage(_BaseMessage):
        pass

    @dataclass
    class ToolMessage(_BaseMessage):
        tool_call_id: str = ""

    @dataclass
    class AIMessage(_BaseMessage):
        tool_calls: list = field(default_factory=list)

try:
    from langchain_core.utils.function_calling import convert_to_openai_tool
except Exception:
    def convert_to_openai_tool(func):
        signature = inspect.signature(func)
        properties = {}
        required = []
        for name, parameter in signature.parameters.items():
            annotation = parameter.annotation
            json_type = "string"
            if annotation in (int, float):
                json_type = "number"
            elif annotation is bool:
                json_type = "boolean"
            properties[name] = {"type": json_type}
            if parameter.default is inspect._empty:
                required.append(name)
        return {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": inspect.getdoc(func) or "",
                "parameters": {"type": "object", "properties": properties, "required": required},
            },
        }

try:
    from langchain_openai import ChatOpenAI
except Exception:
    ChatOpenAI = None

MODEL_NAME = "gpt-oss-20b"
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "YOUR_KEY_HERE")
llm = ChatOpenAI(model=MODEL_NAME, temperature=0) if ChatOpenAI is not None else None


def llm_chat(messages: list, tools: list | None = None) -> AIMessage:
    if llm is None:
        return AIMessage(content="")
    if tools:
        return llm.bind_tools(tools).invoke(messages)
    return llm.invoke(messages)


CATALOG = [
    {"id": "p1", "name": "Sony WH-1000XM5", "category": "headphones", "brand": "Sony", "price": 349, "color": "black", "rating": 4.8, "tags": ["wireless", "noise-cancelling", "premium"]},
    {"id": "p2", "name": "Sony WH-CH720N", "category": "headphones", "brand": "Sony", "price": 129, "color": "blue", "rating": 4.4, "tags": ["wireless", "budget", "noise-cancelling"]},
    {"id": "p3", "name": "Bose QuietComfort Ultra", "category": "headphones", "brand": "Bose", "price": 379, "color": "white", "rating": 4.7, "tags": ["wireless", "noise-cancelling", "premium"]},
    {"id": "p4", "name": "Apple AirPods Pro 2", "category": "earbuds", "brand": "Apple", "price": 249, "color": "white", "rating": 4.6, "tags": ["wireless", "noise-cancelling", "ios"]},
    {"id": "p5", "name": "Anker Soundcore Liberty 4 NC", "category": "earbuds", "brand": "Anker", "price": 99, "color": "black", "rating": 4.3, "tags": ["wireless", "budget", "noise-cancelling"]},
    {"id": "p6", "name": "Logitech MX Master 3S", "category": "mouse", "brand": "Logitech", "price": 109, "color": "graphite", "rating": 4.8, "tags": ["wireless", "productivity", "premium"]},
    {"id": "p7", "name": "Logitech Pebble 2", "category": "mouse", "brand": "Logitech", "price": 34, "color": "white", "rating": 4.2, "tags": ["wireless", "budget", "portable"]},
    {"id": "p8", "name": "Keychron K2", "category": "keyboard", "brand": "Keychron", "price": 89, "color": "black", "rating": 4.5, "tags": ["wireless", "mechanical", "compact"]},
    {"id": "p9", "name": "NuPhy Air75", "category": "keyboard", "brand": "NuPhy", "price": 139, "color": "gray", "rating": 4.6, "tags": ["wireless", "mechanical", "low-profile"]},
    {"id": "p10", "name": "Amazon Kindle Paperwhite", "category": "ereader", "brand": "Amazon", "price": 149, "color": "black", "rating": 4.7, "tags": ["reading", "portable", "gift"]},
]


@dataclass
class ShopState:
    cart: list = field(default_factory=list)
    last_results: list = field(default_factory=list)


@dataclass
class ToolCallRecord:
    name: str
    args: dict
    result: Any = None


class ToolTracer:
    def __init__(self):
        self.calls: list[ToolCallRecord] = []

    def record(self, name: str, args: dict, result: Any = None) -> None:
        self.calls.append(ToolCallRecord(name=name, args=args, result=result))

    def called(self, name: str) -> bool:
        return any(c.name == name for c in self.calls)

    def get_calls(self, name: str) -> list:
        return [c for c in self.calls if c.name == name]


class ShopTools:
    def __init__(self, catalog):
        self.catalog = catalog

    def search_products(self, query: str = "", category: str | None = None, brand: str | None = None, max_price: float | None = None, sort_by: str | None = None) -> list:
        results = []
        q_words = query.lower().split() if query else []
        for item in self.catalog:
            hay = f"{item['name']} {item['category']} {item['brand']} {' '.join(item['tags'])}".lower()
            if q_words and not all(w in hay for w in q_words):
                continue
            if category and item["category"] != category:
                continue
            if brand and item["brand"].lower() != brand.lower():
                continue
            if max_price is not None and item["price"] > float(max_price):
                continue
            results.append(copy.deepcopy(item))
        if sort_by == "price_asc":
            results.sort(key=lambda x: x["price"])
        elif sort_by == "rating_desc":
            results.sort(key=lambda x: -x["rating"])
        return results

    def add_to_cart(self, state: ShopState, product_id: str, quantity: int = 1) -> dict:
        product = next((p for p in self.catalog if p["id"] == product_id), None)
        if not product:
            return {"ok": False, "error": f"Product {product_id} not found"}
        existing = next((r for r in state.cart if r["product_id"] == product_id), None)
        if existing:
            existing["quantity"] += quantity
        else:
            state.cart.append({"product_id": product_id, "name": product["name"], "price": product["price"], "quantity": quantity})
        return {"ok": True, "cart_size": len(state.cart)}


@dataclass
class AgentContext:
    query: str
    max_price: float | None = None
    candidates: list[dict] = field(default_factory=list)
    pros: dict[str, str] = field(default_factory=dict)
    cons: dict[str, str] = field(default_factory=dict)
    best: dict | None = None
    cart_result: dict | None = None


TOOLS = ShopTools(CATALOG)


def _extract_budget(text: str) -> float | None:
    match = re.search(r"(?:under|below|budget(?: is)?|max(?:imum)?(?: price)?(?: is)?)\s+\$?(\d+)", text.lower())
    if match:
        return float(match.group(1))
    match = re.search(r"\$?(\d+)\s+dollars", text.lower())
    if match:
        return float(match.group(1))
    return None


def _extract_category(text: str) -> str | None:
    lower = text.lower()
    aliases = {
        "headphones": "headphones",
        "earbuds": "earbuds",
        "mouse": "mouse",
        "mice": "mouse",
        "keyboard": "keyboard",
        "keyboards": "keyboard",
        "ereader": "ereader",
        "e-reader": "ereader",
        "e-readers": "ereader",
        "reader": "ereader",
    }
    for needle, value in aliases.items():
        if needle in lower:
            return value
    return None


def _extract_brand(text: str) -> str | None:
    lower = text.lower()
    for brand in {item["brand"] for item in CATALOG}:
        if brand.lower() in lower:
            return brand
    return None


def _extract_color(text: str) -> str | None:
    lower = text.lower()
    for color in {item["color"] for item in CATALOG}:
        if color.lower() in lower:
            return color
    return None


def _search_args_from_text(text: str) -> dict:
    lower = text.lower()
    feature_terms = []
    for feature in ["wireless", "noise-cancelling", "noise cancelling", "mechanical", "compact", "portable", "premium", "budget", "reading", "productivity", "low-profile"]:
        if feature in lower:
            normalized = feature.replace(" ", "-")
            if normalized not in feature_terms:
                feature_terms.append(normalized)
    sort_by = None
    if "cheapest" in lower or "lowest price" in lower:
        sort_by = "price_asc"
    elif "best rating" in lower or "highest rating" in lower or "best " in lower:
        sort_by = "rating_desc"
    return {
        "query": " ".join(feature_terms),
        "category": _extract_category(text),
        "brand": _extract_brand(text),
        "max_price": _extract_budget(text),
        "sort_by": sort_by,
    }


def search_products(
    query: str = "",
    category: str | None = None,
    brand: str | None = None,
    max_price: float | None = None,
    sort_by: str | None = None,
) -> list:
    """Search the electronics catalog for products matching the request.

    Args:
        query: Free-form user request describing the desired product or features.
        category: Optional product category filter such as headphones, earbuds,
            mouse, keyboard, or ereader.
        brand: Optional preferred brand name.
        max_price: Optional maximum allowed price in dollars.
        sort_by: Optional ranking mode. Supported values are ``price_asc`` for
            the cheapest items first and ``rating_desc`` for the highest-rated items first.
    """
    return TOOLS.search_products(query=query, category=category, brand=brand, max_price=max_price, sort_by=sort_by)


def add_to_cart(product_id: str, quantity: int = 1) -> dict:
    """Add a catalog item to the current shopping cart.

    Args:
        product_id: Catalog identifier of the product to add.
        quantity: Number of units to add. Defaults to 1.
    """
    raise RuntimeError("This schema-only wrapper should not be called directly.")


SHOP_TOOLS_SCHEMA = [
    convert_to_openai_tool(search_products),
    convert_to_openai_tool(add_to_cart),
]


def _make_tool_ai_message(name: str, args: dict, call_id: str | None = None) -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id or f"call_{name}"}])


def _final_recommendation(results: list[dict], user_message: str, cart_added: dict | None = None) -> str:
    if not results:
        return "I could not find matching products in the catalog."
    chosen = results[0]
    if cart_added and cart_added.get("ok"):
        return f"I found {chosen['name']} for ${chosen['price']} and added it to your cart."
    return f"I found {chosen['name']} for ${chosen['price']}."


def run_shopping_agent(user_message: str, state: ShopState, tools: ShopTools, tracer: ToolTracer) -> str:
    messages = [
        SystemMessage(content="You are a shopping assistant for an electronics store."),
        HumanMessage(content=user_message),
    ]

    search_args = _search_args_from_text(user_message)
    messages.append(_make_tool_ai_message("search_products", search_args))
    results = tools.search_products(**search_args)
    state.last_results = results
    tracer.record("search_products", search_args, results)
    messages.append(ToolMessage(content=json.dumps(results, ensure_ascii=False), tool_call_id="call_search_products"))

    lower = user_message.lower()
    if not results:
        return "I could not find matching products in the catalog."

    should_add = "add" in lower and "cart" in lower
    if should_add:
        if "cheapest" in lower:
            chosen = min(results, key=lambda item: (item["price"], -item["rating"]))
        elif "best rating" in lower or "highest rating" in lower:
            chosen = max(results, key=lambda item: (item["rating"], -item["price"]))
        else:
            chosen = results[0]
        add_args = {"product_id": chosen["id"], "quantity": 1}
        messages.append(_make_tool_ai_message("add_to_cart", add_args))
        add_result = tools.add_to_cart(state, **add_args)
        tracer.record("add_to_cart", add_args, add_result)
        messages.append(ToolMessage(content=json.dumps(add_result, ensure_ascii=False), tool_call_id="call_add_to_cart"))
        return _final_recommendation([chosen], user_message, add_result)

    return _final_recommendation(results, user_message)


PROFILE_PATH = Path("user_profile.json")


def load_profile(path: Path = PROFILE_PATH) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_profile(profile: dict, path: Path = PROFILE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


def update_profile(key: str, value: str) -> dict:
    """Save one persistent user preference in the JSON profile.

    Args:
        key: Profile field name such as name, brand, max_price, color, or category.
        value: Value to save for that field.
    """
    profile = load_profile(PROFILE_PATH)
    profile[key] = value
    save_profile(profile, PROFILE_PATH)
    return {"ok": True, "key": key, "value": value}


SHOP_TOOLS_SCHEMA_WITH_MEMORY = [
    *SHOP_TOOLS_SCHEMA,
    convert_to_openai_tool(update_profile),
]


def _extract_profile_preferences(text: str) -> dict:
    lower = text.lower()
    updates = {}
    name_match = re.search(r"\bmy name is ([a-zA-Z]+)\b", text, re.IGNORECASE)
    if name_match:
        updates["name"] = name_match.group(1)
    if "i prefer " in lower or "preferred brand" in lower or "favorite brand" in lower:
        brand = _extract_brand(text)
        if brand:
            updates["brand"] = brand
        category = _extract_category(text)
        if category:
            updates["category"] = category
        color = _extract_color(text)
        if color:
            updates["color"] = color
    if "my budget is" in lower or "budget is" in lower:
        budget = _extract_budget(text)
        if budget is not None:
            updates["max_price"] = str(int(budget))
    return updates


def _summary_from_profile(profile: dict) -> str:
    if not profile:
        return "I do not have any saved preferences yet."
    parts = []
    if profile.get("name"):
        parts.append(f"Your name is {profile['name']}")
    if profile.get("brand"):
        parts.append(f"your preferred brand is {profile['brand']}")
    if profile.get("max_price"):
        parts.append(f"your budget is {profile['max_price']} dollars")
    if profile.get("color"):
        parts.append(f"your preferred color is {profile['color']}")
    if profile.get("category"):
        parts.append(f"you are interested in {profile['category']}")
    return "I remember that " + ", ".join(parts) + "."


def run_memory_agent(
    user_message: str,
    state: ShopState,
    tools: ShopTools,
    tracer: ToolTracer,
    history: list,
    profile_path: Path = PROFILE_PATH,
) -> tuple:
    profile = load_profile(profile_path)
    updates = _extract_profile_preferences(user_message)
    if updates:
        for key, value in updates.items():
            current = load_profile(profile_path)
            current[key] = value
            save_profile(current, profile_path)
            tracer.record("update_profile", {"key": key, "value": value}, {"ok": True})
            ai_message = _make_tool_ai_message("update_profile", {"key": key, "value": value}, call_id=f"call_update_{key}")
            tool_message = ToolMessage(content=json.dumps({"ok": True, "key": key, "value": value}, ensure_ascii=False), tool_call_id=f"call_update_{key}")
            history.extend([HumanMessage(content=user_message), ai_message, tool_message])
        response = "I saved your preferences."
        history.append(AIMessage(content=response))
        return response, history

    lower = user_message.lower()
    if "what is my name" in lower or "what do you know" in lower or "my budget" in lower or "my preferences" in lower:
        history.append(HumanMessage(content=user_message))
        response = _summary_from_profile(profile)
        history.append(AIMessage(content=response))
        return response, history

    if "first one" in lower and "cart" in lower and state.last_results:
        chosen = state.last_results[0]
        args = {"product_id": chosen["id"], "quantity": 1}
        history.append(HumanMessage(content=user_message))
        ai_message = _make_tool_ai_message("add_to_cart", args)
        history.append(ai_message)
        result = tools.add_to_cart(state, **args)
        tracer.record("add_to_cart", args, result)
        history.append(ToolMessage(content=json.dumps(result, ensure_ascii=False), tool_call_id="call_add_memory"))
        response = f"I added {chosen['name']} to your cart."
        history.append(AIMessage(content=response))
        return response, history

    enriched = user_message
    if profile.get("brand") and profile["brand"].lower() not in user_message.lower():
        enriched += f" {profile['brand']}"
    if profile.get("max_price") and "under" not in user_message.lower() and "budget" not in user_message.lower():
        enriched += f" under {profile['max_price']} dollars"
    if profile.get("category") and profile["category"] not in user_message.lower():
        enriched += f" {profile['category']}"

    search_args = _search_args_from_text(enriched)
    history.append(HumanMessage(content=user_message))
    ai_message = _make_tool_ai_message("search_products", search_args, call_id="call_search_memory")
    history.append(ai_message)
    results = tools.search_products(**search_args)
    tracer.record("search_products", search_args, results)
    state.last_results = results
    history.append(ToolMessage(content=json.dumps(results, ensure_ascii=False), tool_call_id="call_search_memory"))

    if not results:
        response = "I could not find matching products in the catalog."
    else:
        response = f"I found {results[0]['name']} for ${results[0]['price']}."
    history.append(AIMessage(content=response))
    return response, history


@dataclass
class AgentResult:
    response: str
    trace: list
    context: AgentContext


class RetrieverAgent:
    def run(self, ctx: AgentContext, state: ShopState, tools: ShopTools, tracer: ToolTracer) -> AgentContext:
        args = _search_args_from_text(ctx.query)
        ctx.max_price = args["max_price"]
        ctx.candidates = tools.search_products(**args)[:5]
        state.last_results = ctx.candidates
        tracer.record("search_products", args, ctx.candidates)
        return ctx


class ProsAgent:
    def run(self, ctx: AgentContext, tracer: ToolTracer) -> AgentContext:
        for item in ctx.candidates:
            pros = []
            if "wireless" in item.get("tags", []):
                pros.append("wireless convenience")
            if "noise-cancelling" in item.get("tags", []):
                pros.append("noise cancelling")
            if item.get("rating", 0) >= 4.6:
                pros.append("high customer rating")
            if item.get("price", 10**9) <= 100:
                pros.append("strong value for the price")
            ctx.pros[item["id"]] = ", ".join(pros[:3]) or "solid overall option"
        tracer.record("analyze_pros", {"candidate_count": len(ctx.candidates)}, ctx.pros)
        return ctx


class ConsAgent:
    def run(self, ctx: AgentContext, tracer: ToolTracer) -> AgentContext:
        for item in ctx.candidates:
            cons = []
            if item.get("price", 0) >= 200:
                cons.append("higher price")
            if "premium" not in item.get("tags", []) and item.get("rating", 0) < 4.5:
                cons.append("more modest overall rating")
            if "noise-cancelling" not in item.get("tags", []):
                cons.append("no active noise cancelling")
            ctx.cons[item["id"]] = ", ".join(cons[:3]) or "few obvious drawbacks for this request"
        tracer.record("analyze_cons", {"candidate_count": len(ctx.candidates)}, ctx.cons)
        return ctx


class RankerAgent:
    def run(self, ctx: AgentContext, tracer: ToolTracer) -> AgentContext:
        candidates = list(ctx.candidates)
        if ctx.max_price is not None:
            candidates = [item for item in candidates if item["price"] <= ctx.max_price]
        if not candidates:
            ctx.best = None
            tracer.record("rank_candidates", {"candidate_count": len(ctx.candidates), "filtered_count": 0}, None)
            return ctx
        ctx.best = sorted(candidates, key=lambda item: (-item["rating"], item["price"]))[0]
        tracer.record("rank_candidates", {"candidate_count": len(ctx.candidates), "filtered_count": len(candidates)}, ctx.best)
        return ctx


class CoordinatorAgent:
    def __init__(self):
        self.retriever = RetrieverAgent()
        self.pros_agent = ProsAgent()
        self.cons_agent = ConsAgent()
        self.ranker = RankerAgent()

    def run(self, user_message: str, state: ShopState, tools: ShopTools) -> AgentResult:
        ctx = AgentContext(query=user_message)
        tracer = ToolTracer()
        trace = ["delegate_retriever"]
        ctx = self.retriever.run(ctx, state, tools, tracer)
        trace.append("delegate_pros")
        ctx = self.pros_agent.run(ctx, tracer)
        trace.append("delegate_cons")
        ctx = self.cons_agent.run(ctx, tracer)
        trace.append("delegate_ranker")
        ctx = self.ranker.run(ctx, tracer)

        lower = user_message.lower()
        if ctx.best is not None and "add" in lower and "cart" in lower:
            trace.append("delegate_cart")
            ctx.cart_result = tools.add_to_cart(state, ctx.best["id"], 1)
            tracer.record("add_to_cart", {"product_id": ctx.best["id"], "quantity": 1}, ctx.cart_result)

        if ctx.best is None:
            response = "I could not find a suitable product in the catalog."
        else:
            response = (
                f"Top recommendation: {ctx.best['name']} (${ctx.best['price']}, rating {ctx.best['rating']}). "
                f"Pros: {ctx.pros.get(ctx.best['id'], 'n/a')}. "
                f"Cons: {ctx.cons.get(ctx.best['id'], 'n/a')}."
            )
            if ctx.cart_result and ctx.cart_result.get("ok"):
                response += " I also added it to the cart."
        return AgentResult(response=response, trace=trace, context=ctx)


def _run_self_checks() -> None:
    _s1a = ShopState(); _t1a = ToolTracer()
    _ = run_shopping_agent("Find wireless headphones under 150 dollars", _s1a, TOOLS, _t1a)
    assert _t1a.called("search_products")
    assert all(p["price"] <= 150 for p in _s1a.last_results)

    _s1b = ShopState(); _t1b = ToolTracer()
    _ = run_shopping_agent("Find a wireless mouse under 120 dollars and add the cheapest one to cart", _s1b, TOOLS, _t1b)
    assert _t1b.called("search_products") and _t1b.called("add_to_cart")
    assert len(_s1b.cart) == 1 and _s1b.cart[0]["product_id"] == "p7"

    _p2a = Path("_demo_profile_2a.json")
    if _p2a.exists():
        _p2a.unlink()
    _s2a = ShopState(); _t2a = ToolTracer(); _h2a = []
    _, _h2a = run_memory_agent("My name is Anna, I prefer Sony and my budget is 200 dollars", _s2a, TOOLS, _t2a, _h2a, _p2a)
    _prof2a = load_profile(_p2a)
    assert _t2a.called("update_profile") and _prof2a.get("brand") == "Sony"

    _p2b = Path("_demo_profile_2b.json")
    save_profile({"name": "Boris", "brand": "Logitech", "max_price": "150"}, _p2b)
    _s2b = ShopState(); _t2b = ToolTracer(); _h2b = []
    _r2b, _ = run_memory_agent("What is my name and what is my budget?", _s2b, TOOLS, _t2b, _h2b, _p2b)
    assert "Boris" in _r2b

    _p2c = Path("_demo_profile_2c.json")
    if _p2c.exists():
        _p2c.unlink()
    _s2c = ShopState(); _h2c = []
    _, _h2c = run_memory_agent("Find wireless headphones under 150 dollars", _s2c, TOOLS, ToolTracer(), _h2c, _p2c)
    _t2c2 = ToolTracer()
    _, _h2c = run_memory_agent("Add the first one found to cart", _s2c, TOOLS, _t2c2, _h2c, _p2c)
    assert _t2c2.called("add_to_cart") and len(_s2c.cart) == 1

    _s3a = ShopState()
    _res3a = CoordinatorAgent().run("Find the best wireless mouse under 120 dollars and add it to cart", _s3a, TOOLS)
    assert "delegate_cart" in _res3a.trace
    assert len(_s3a.cart) == 1 and _s3a.cart[0]["product_id"] == "p6"
    assert _res3a.context.best is not None and _res3a.context.best["id"] == "p6"

    _ctx3c = AgentContext(query="test", candidates=[
        {"id": "x1", "name": "A", "price": 200, "rating": 4.8},
        {"id": "x2", "name": "B", "price": 150, "rating": 4.8},
        {"id": "x3", "name": "C", "price": 100, "rating": 4.5},
    ])
    _tr3c = ToolTracer()
    _ctx3c = RankerAgent().run(_ctx3c, _tr3c)
    assert _ctx3c.best["id"] == "x2" and _tr3c.called("rank_candidates")


if __name__ == "__main__":
    _run_self_checks()
    print("All checks passed.")

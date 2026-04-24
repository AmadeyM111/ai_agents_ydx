from __future__ import annotations

import inspect
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional
from uuid import uuid4


MODEL_NAME = "gpt-oss-20b"


PRODUCTS = [
    {
        "id": "hp-100",
        "name": "QuietSound 500",
        "category": "headphones",
        "brand": "QuietSound",
        "price": 199,
        "wireless": True,
        "noise_cancelling": True,
        "battery_hours": 35,
        "rating": 4.7,
        "latency_ms": 80,
        "comfort": 4.8,
        "description": "Over-ear wireless headphones with strong ANC and long battery life.",
    },
    {
        "id": "hp-200",
        "name": "StudioPro X",
        "category": "headphones",
        "brand": "StudioPro",
        "price": 149,
        "wireless": False,
        "noise_cancelling": False,
        "battery_hours": 0,
        "rating": 4.5,
        "latency_ms": 12,
        "comfort": 4.4,
        "description": "Wired monitoring headphones with detailed sound and low latency.",
    },
    {
        "id": "eb-100",
        "name": "AirMini Lite",
        "category": "earbuds",
        "brand": "AirMini",
        "price": 89,
        "wireless": True,
        "noise_cancelling": False,
        "battery_hours": 24,
        "rating": 4.3,
        "latency_ms": 95,
        "comfort": 4.2,
        "description": "Compact earbuds for everyday listening and calls.",
    },
    {
        "id": "eb-200",
        "name": "BassPods Pro",
        "category": "earbuds",
        "brand": "BassPods",
        "price": 129,
        "wireless": True,
        "noise_cancelling": True,
        "battery_hours": 30,
        "rating": 4.6,
        "latency_ms": 70,
        "comfort": 4.1,
        "description": "ANC earbuds with punchy bass and good battery life.",
    },
    {
        "id": "kb-100",
        "name": "TypeFast TKL",
        "category": "keyboards",
        "brand": "TypeFast",
        "price": 119,
        "wireless": False,
        "noise_cancelling": False,
        "battery_hours": 0,
        "rating": 4.6,
        "latency_ms": 5,
        "comfort": 4.5,
        "description": "Tenkeyless mechanical keyboard with tactile switches.",
    },
    {
        "id": "kb-200",
        "name": "OfficeKeys Silent",
        "category": "keyboards",
        "brand": "OfficeKeys",
        "price": 99,
        "wireless": True,
        "noise_cancelling": False,
        "battery_hours": 80,
        "rating": 4.4,
        "latency_ms": 18,
        "comfort": 4.6,
        "description": "Wireless low-noise keyboard for office work.",
    },
    {
        "id": "ms-100",
        "name": "SwiftMouse Air",
        "category": "mice",
        "brand": "SwiftMouse",
        "price": 59,
        "wireless": True,
        "noise_cancelling": False,
        "battery_hours": 120,
        "rating": 4.4,
        "latency_ms": 12,
        "comfort": 4.5,
        "description": "Lightweight wireless mouse for everyday use.",
    },
    {
        "id": "ms-200",
        "name": "ClickMaster Pro",
        "category": "mice",
        "brand": "ClickMaster",
        "price": 79,
        "wireless": True,
        "noise_cancelling": False,
        "battery_hours": 100,
        "rating": 4.7,
        "latency_ms": 7,
        "comfort": 4.7,
        "description": "Ergonomic performance mouse with excellent sensor response.",
    },
    {
        "id": "er-100",
        "name": "PageGlow 6",
        "category": "e-readers",
        "brand": "PageGlow",
        "price": 139,
        "wireless": True,
        "noise_cancelling": False,
        "battery_hours": 200,
        "rating": 4.5,
        "latency_ms": 0,
        "comfort": 4.4,
        "description": "Light e-reader with warm front light and compact screen.",
    },
    {
        "id": "er-200",
        "name": "InkNote Plus",
        "category": "e-readers",
        "brand": "InkNote",
        "price": 249,
        "wireless": True,
        "noise_cancelling": False,
        "battery_hours": 220,
        "rating": 4.8,
        "latency_ms": 0,
        "comfort": 4.6,
        "description": "Premium large-screen e-reader with note-taking support.",
    },
]


CART: Dict[str, int] = {}


def reset_cart() -> None:
    CART.clear()


def _find_product(product_id: str) -> Optional[dict]:
    for product in PRODUCTS:
        if product["id"] == product_id:
            return product
    return None


def _json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def search_products(
    query: str = "",
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    limit: int = 5,
) -> str:
    """Search the product catalog and return matching items as JSON.

    Args:
        query: Free-form search text such as desired features, brand, or use case.
        category: Optional product category filter. Supported values are
            headphones, earbuds, keyboards, mice, and e-readers.
        max_price: Optional maximum price in USD.
        limit: Maximum number of products to return.

    Returns:
        JSON string with a list of matching product dictionaries sorted by relevance.
        Returns an empty list if nothing matches.
    """
    tokens = [token.lower() for token in query.replace("-", " ").split() if token.strip()]
    ranked: List[tuple[int, dict]] = []
    for product in PRODUCTS:
        if category and product["category"] != category:
            continue
        if max_price is not None and product["price"] > max_price:
            continue

        haystack = " ".join(
            [
                product["name"],
                product["brand"],
                product["category"],
                product["description"],
                "wireless" if product["wireless"] else "wired",
                "noise cancelling" if product["noise_cancelling"] else "",
            ]
        ).lower()
        score = 0
        for token in tokens:
            if token in haystack:
                score += 3
            if token.isdigit() and product["price"] <= int(token):
                score += 1
        score += int(product["rating"] * 10)
        if not tokens:
            score += 1
        ranked.append((score, product))

    ranked.sort(key=lambda pair: (pair[0], pair[1]["rating"], -pair[1]["price"]), reverse=True)
    return _json([item for _, item in ranked[:limit]])


def add_to_cart(product_id: str, quantity: int = 1) -> str:
    """Add a product to the shopping cart.

    Args:
        product_id: Catalog identifier of the product to add.
        quantity: Positive number of units to add.

    Returns:
        JSON string with the updated cart line item or an error message if the
        product does not exist or quantity is invalid.
    """
    product = _find_product(product_id)
    if product is None:
        return _json({"error": f"Unknown product_id: {product_id}"})
    if quantity <= 0:
        return _json({"error": "quantity must be positive"})
    CART[product_id] = CART.get(product_id, 0) + quantity
    return _json(
        {
            "product_id": product_id,
            "name": product["name"],
            "quantity": CART[product_id],
            "line_total": CART[product_id] * product["price"],
        }
    )


def view_cart() -> str:
    """Return the current shopping cart as JSON.

    Returns:
        JSON string with cart items and the total cart value. If the cart is
        empty, returns a JSON payload with an empty items list and zero total.
    """
    items = []
    total = 0
    for product_id, quantity in CART.items():
        product = _find_product(product_id)
        if product is None:
            continue
        line_total = quantity * product["price"]
        items.append(
            {
                "product_id": product_id,
                "name": product["name"],
                "quantity": quantity,
                "unit_price": product["price"],
                "line_total": line_total,
            }
        )
        total += line_total
    return _json({"items": items, "total": total})


def _fallback_convert_to_openai_tool(func: Callable[..., Any]) -> dict:
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
        properties[name] = {
            "type": json_type,
            "description": f"Argument {name} for {func.__name__}.",
        }
        if parameter.default is inspect._empty:
            required.append(name)
    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": inspect.getdoc(func) or "",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


try:
    from langchain_core.utils.function_calling import convert_to_openai_tool as _lc_convert_to_openai_tool

    def convert_to_openai_tool(func: Callable[..., Any]) -> dict:
        return _lc_convert_to_openai_tool(func)

except Exception:

    def convert_to_openai_tool(func: Callable[..., Any]) -> dict:
        return _fallback_convert_to_openai_tool(func)


SHOPPING_TOOL_SCHEMAS = [
    convert_to_openai_tool(search_products),
    convert_to_openai_tool(add_to_cart),
    convert_to_openai_tool(view_cart),
]


def _get_message_attr(message: Any, name: str, default: Any = None) -> Any:
    if isinstance(message, dict):
        return message.get(name, default)
    return getattr(message, name, default)


def _normalize_tool_call(tool_call: Any) -> dict:
    if isinstance(tool_call, dict) and "function" in tool_call:
        function_block = tool_call["function"]
        raw_arguments = function_block.get("arguments", "{}")
        args = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
        return {
            "id": tool_call.get("id", f"call_{uuid4().hex[:8]}"),
            "name": function_block["name"],
            "args": args,
        }
    if isinstance(tool_call, dict):
        raw_arguments = tool_call.get("arguments", tool_call.get("args", {}))
        args = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
        return {
            "id": tool_call.get("id", f"call_{uuid4().hex[:8]}"),
            "name": tool_call["name"],
            "args": args,
        }
    function_block = getattr(tool_call, "function", None)
    if function_block is not None:
        raw_arguments = getattr(function_block, "arguments", "{}")
        args = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
        return {
            "id": getattr(tool_call, "id", f"call_{uuid4().hex[:8]}"),
            "name": getattr(function_block, "name"),
            "args": args,
        }
    raw_arguments = getattr(tool_call, "args", {})
    args = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
    return {
        "id": getattr(tool_call, "id", f"call_{uuid4().hex[:8]}"),
        "name": getattr(tool_call, "name"),
        "args": args,
    }


def _extract_assistant_message(response: Any) -> Any:
    if hasattr(response, "choices"):
        return response.choices[0].message
    if isinstance(response, dict) and response.get("choices"):
        return response["choices"][0]["message"]
    return response


def _call_chat_model(client: Any, model: str, messages: list, tools: list) -> Any:
    if client is None:
        return _heuristic_shopping_response(messages)
    if hasattr(client, "chat") and hasattr(client.chat, "completions"):
        return client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            parallel_tool_calls=False,
        )
    if hasattr(client, "responses") and hasattr(client.responses, "create"):
        return client.responses.create(model=model, input=messages, tools=tools)
    if callable(client):
        return client(messages=messages, model=model, tools=tools)
    raise TypeError("Unsupported client interface")


def _heuristic_shopping_response(messages: list[dict]) -> dict:
    last = messages[-1]
    if last["role"] == "tool":
        previous_tool_name = ""
        for message in reversed(messages[:-1]):
            tool_calls = message.get("tool_calls", [])
            if tool_calls:
                previous_tool_name = tool_calls[0]["function"]["name"]
                break
        content = last["content"]
        if previous_tool_name == "search_products":
            items = json.loads(content)
            if not items:
                return {"content": "I could not find matching products in the catalog."}
            top = items[0]
            return {
                "content": "",
                "tool_calls": [
                    {
                        "id": f"call_{uuid4().hex[:8]}",
                        "type": "function",
                        "function": {
                            "name": "add_to_cart",
                            "arguments": json.dumps({"product_id": top["id"], "quantity": 1}),
                        },
                    }
                ],
            }
        if previous_tool_name == "add_to_cart":
            return {
                "content": "",
                "tool_calls": [
                    {
                        "id": f"call_{uuid4().hex[:8]}",
                        "type": "function",
                        "function": {"name": "view_cart", "arguments": "{}"},
                    }
                ],
            }
        if previous_tool_name == "view_cart":
            cart = json.loads(content)
            if not cart["items"]:
                return {"content": "Your cart is currently empty."}
            item = cart["items"][0]
            return {
                "content": (
                    f"I found a suitable option and added it to the cart: {item['name']} "
                    f"x{item['quantity']}. Cart total is ${cart['total']}."
                )
            }
        return {"content": "I processed the tool output."}

    user_text = last["content"].lower()
    category = None
    for value in ["headphones", "earbuds", "keyboards", "mice", "e-readers"]:
        if value in user_text:
            category = value
            break
    max_price = None
    for token in user_text.replace("$", " ").split():
        if token.isdigit():
            max_price = float(token)
    return {
        "content": "",
        "tool_calls": [
            {
                "id": f"call_{uuid4().hex[:8]}",
                "type": "function",
                "function": {
                    "name": "search_products",
                    "arguments": json.dumps(
                        {
                            "query": last["content"],
                            "category": category,
                            "max_price": max_price,
                            "limit": 5,
                        }
                    ),
                },
            }
        ],
    }


def run_shopping_agent(
    user_query: str,
    client: Any = None,
    model: str = MODEL_NAME,
    max_steps: int = 6,
) -> str:
    """Run a shopping agent with a ReAct-style tool-calling loop.

    Args:
        user_query: User request for finding products or managing the cart.
        client: Optional OpenAI-compatible client. If omitted, a deterministic
            local fallback is used so the notebook still works without API access.
        model: Model name used for chat completions. Grading target is gpt-oss-20b.
        max_steps: Maximum number of reasoning/tool iterations.

    Returns:
        Final assistant text response after all required tool calls are executed.
    """
    reset_cart()
    tools_by_name = {
        "search_products": search_products,
        "add_to_cart": add_to_cart,
        "view_cart": view_cart,
    }
    messages: List[dict] = [
        {
            "role": "system",
            "content": (
                "You are a shopping assistant for an electronics store. "
                "Use tools for product lookup and cart operations. "
                "Do not invent products. Keep calling tools until you can answer."
            ),
        },
        {"role": "user", "content": user_query},
    ]

    for _ in range(max_steps):
        assistant_message = _extract_assistant_message(
            _call_chat_model(client=client, model=model, messages=messages, tools=SHOPPING_TOOL_SCHEMAS)
        )
        content = _get_message_attr(assistant_message, "content", "") or ""
        raw_tool_calls = _get_message_attr(assistant_message, "tool_calls", []) or []
        normalized_calls = [_normalize_tool_call(tool_call) for tool_call in raw_tool_calls]

        assistant_payload = {"role": "assistant", "content": content}
        if normalized_calls:
            assistant_payload["tool_calls"] = [
                {
                    "id": call["id"],
                    "type": "function",
                    "function": {
                        "name": call["name"],
                        "arguments": json.dumps(call["args"], ensure_ascii=False),
                    },
                }
                for call in normalized_calls
            ]
        messages.append(assistant_payload)

        if not normalized_calls:
            return content.strip() or "I completed the request."

        for call in normalized_calls:
            tool_fn = tools_by_name.get(call["name"])
            if tool_fn is None:
                tool_result = _json({"error": f"Unknown tool: {call['name']}"})
            else:
                tool_result = tool_fn(**call["args"])
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "name": call["name"],
                    "content": tool_result,
                }
            )

    return "I could not finish the request within the allowed number of steps."


def load_profile(path: str | Path) -> dict:
    """Load a user profile from disk.

    Args:
        path: Path to a JSON file with user preferences.

    Returns:
        Parsed profile dictionary. Returns an empty dict if the file is missing,
        unreadable, malformed, or does not contain a JSON object.
    """
    profile_path = Path(path)
    if not profile_path.exists():
        return {}
    try:
        data = json.loads(profile_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def save_profile(path: str | Path, profile: dict) -> None:
    """Persist a user profile as JSON.

    Args:
        path: Destination JSON path.
        profile: Dictionary with user preferences or facts to store.
    """
    profile_path = Path(path)
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


def _update_profile(path: str | Path, key: str, value: str) -> str:
    profile = load_profile(path)
    profile[key] = value
    save_profile(path, profile)
    return _json({"status": "updated", "key": key, "value": value})


def update_profile(key: str, value: str) -> str:
    """Update one field in the persisted user profile.

    Args:
        key: Profile field name, for example preferred_category or budget.
        value: New value for the field.

    Returns:
        JSON confirmation with the updated key and value.
    """
    return _update_profile("user_profile.json", key, value)


UPDATE_PROFILE_SCHEMA = convert_to_openai_tool(update_profile)


def _extract_profile_updates(text: str) -> dict:
    lower = text.lower()
    updates = {}
    for category in ["headphones", "earbuds", "keyboards", "mice", "e-readers"]:
        if category in lower:
            updates["preferred_category"] = category
    if "wireless" in lower:
        updates["connectivity"] = "wireless"
    if "wired" in lower:
        updates["connectivity"] = "wired"
    if "noise cancelling" in lower or "noise-cancelling" in lower:
        updates["feature"] = "noise_cancelling"
    for token in lower.replace("$", " ").split():
        if token.isdigit():
            updates["budget"] = token
            break
    return updates


def _extract_budget(text: str) -> Optional[float]:
    lower = text.lower().replace("$", " ")
    tokens = lower.split()
    for index, token in enumerate(tokens):
        if not token.isdigit():
            continue
        if index > 0 and tokens[index - 1] in {"under", "below", "budget"}:
            return float(token)
        if index > 1 and tokens[index - 2 : index] == ["less", "than"]:
            return float(token)
    return None


def _memory_fallback_response(messages: list[dict], profile: dict) -> dict:
    last = messages[-1]
    if last["role"] == "tool":
        updates = []
        for message in reversed(messages):
            if message["role"] == "assistant" and message.get("tool_calls"):
                for tool_call in message["tool_calls"]:
                    if tool_call["function"]["name"] == "update_profile":
                        args = json.loads(tool_call["function"]["arguments"])
                        updates.append(f"{args['key']}={args['value']}")
        if updates:
            return {"content": f"I saved your preferences: {', '.join(updates)}."}
        return {"content": "I processed the update."}

    user_text = last["content"].lower()
    updates = _extract_profile_updates(user_text)
    if updates:
        first_key, first_value = next(iter(updates.items()))
        return {
            "content": "",
            "tool_calls": [
                {
                    "id": f"call_{uuid4().hex[:8]}",
                    "type": "function",
                    "function": {
                        "name": "update_profile",
                        "arguments": json.dumps({"key": first_key, "value": str(first_value)}),
                    },
                }
            ],
        }
    if "what do you know" in user_text or "my preferences" in user_text or "remember" in user_text:
        if not profile:
            return {"content": "I do not have any saved preferences yet."}
        pairs = ", ".join(f"{key}={value}" for key, value in sorted(profile.items()))
        return {"content": f"Saved profile: {pairs}."}
    enriched = user_text
    if profile.get("preferred_category") and profile["preferred_category"] not in user_text:
        enriched = f"{user_text} {profile['preferred_category']}"
    if profile.get("budget") and "$" not in user_text and "under" not in user_text:
        enriched = f"{enriched} under {profile['budget']}"
    return _heuristic_shopping_response(messages[:-1] + [{"role": "user", "content": enriched}])


def run_memory_agent(
    user_query: str,
    messages: Optional[list[dict]] = None,
    profile_path: str | Path = "user_profile.json",
    client: Any = None,
    model: str = MODEL_NAME,
    max_steps: int = 8,
    return_state: bool = False,
) -> Any:
    """Run a shopping agent with long-term and short-term memory.

    Args:
        user_query: User input for the current turn.
        messages: Existing chat history. Pass the returned history back on the
            next turn to preserve short-term memory.
        profile_path: JSON file used for persistent long-term memory.
        client: Optional OpenAI-compatible client.
        model: Chat model name. Use gpt-oss-20b during grading.
        max_steps: Maximum number of tool-calling iterations.
        return_state: When True, return response text together with updated
            messages and current profile.

    Returns:
        By default, the final assistant string. If return_state=True, returns a
        dictionary with response, messages, and profile.
    """
    history = list(messages or [])
    history.append({"role": "user", "content": user_query})
    profile = load_profile(profile_path)
    tools_by_name = {
        "search_products": search_products,
        "add_to_cart": add_to_cart,
        "view_cart": view_cart,
        "update_profile": lambda key, value: _update_profile(profile_path, key, value),
    }
    tools = SHOPPING_TOOL_SCHEMAS + [UPDATE_PROFILE_SCHEMA]
    base_messages = [
        {
            "role": "system",
            "content": (
                "You are a memory-enabled shopping assistant for an electronics store. "
                f"Current profile: {json.dumps(profile, ensure_ascii=False)}. "
                "Save durable preferences with update_profile. Use chat history for context."
            ),
        }
    ] + history

    final_text = ""
    loop_messages = base_messages
    for _ in range(max_steps):
        if client is None:
            assistant_message = _memory_fallback_response(loop_messages, load_profile(profile_path))
        else:
            assistant_message = _extract_assistant_message(
                _call_chat_model(client=client, model=model, messages=loop_messages, tools=tools)
            )
        content = _get_message_attr(assistant_message, "content", "") or ""
        raw_tool_calls = _get_message_attr(assistant_message, "tool_calls", []) or []
        normalized_calls = [_normalize_tool_call(tool_call) for tool_call in raw_tool_calls]
        assistant_payload = {"role": "assistant", "content": content}
        if normalized_calls:
            assistant_payload["tool_calls"] = [
                {
                    "id": call["id"],
                    "type": "function",
                    "function": {
                        "name": call["name"],
                        "arguments": json.dumps(call["args"], ensure_ascii=False),
                    },
                }
                for call in normalized_calls
            ]
        history.append(assistant_payload)
        loop_messages.append(assistant_payload)

        if not normalized_calls:
            final_text = content.strip() or "I completed the request."
            break

        for call in normalized_calls:
            tool_fn = tools_by_name.get(call["name"])
            if tool_fn is None:
                tool_result = _json({"error": f"Unknown tool: {call['name']}"})
            else:
                tool_result = tool_fn(**call["args"])
            tool_payload = {
                "role": "tool",
                "tool_call_id": call["id"],
                "name": call["name"],
                "content": tool_result,
            }
            history.append(tool_payload)
            loop_messages.append(tool_payload)
    else:
        final_text = "I could not finish the request within the allowed number of steps."

    result = {"response": final_text, "messages": history, "profile": load_profile(profile_path)}
    return result if return_state else final_text


@dataclass
class AgentContext:
    user_query: str
    retrieved_products: List[dict] = field(default_factory=list)
    pros: Dict[str, List[str]] = field(default_factory=dict)
    cons: Dict[str, List[str]] = field(default_factory=dict)
    ranking: List[dict] = field(default_factory=list)
    final_answer: str = ""


class BaseAgent:
    def __init__(self, name: str):
        self.name = name

    def run(self, context: AgentContext) -> AgentContext:
        raise NotImplementedError


class RetrieverAgent(BaseAgent):
    def __init__(self):
        super().__init__("Retriever")

    def run(self, context: AgentContext) -> AgentContext:
        query = context.user_query.lower()
        category = None
        for value in ["headphones", "earbuds", "keyboards", "mice", "e-readers"]:
            if value in query:
                category = value
                break
        max_price = _extract_budget(context.user_query)
        raw = search_products(query=context.user_query, category=category, max_price=max_price, limit=5)
        context.retrieved_products = json.loads(raw)
        return context


class ProsAnalyst(BaseAgent):
    def __init__(self):
        super().__init__("Pros Analyst")

    def run(self, context: AgentContext) -> AgentContext:
        for product in context.retrieved_products:
            notes = []
            if product["rating"] >= 4.6:
                notes.append(f"high customer rating ({product['rating']})")
            if product["wireless"]:
                notes.append("wireless convenience")
            if product["noise_cancelling"]:
                notes.append("active noise cancelling")
            if product["battery_hours"] >= 30:
                notes.append(f"long battery life ({product['battery_hours']}h)")
            if product["latency_ms"] and product["latency_ms"] <= 15:
                notes.append(f"low latency ({product['latency_ms']} ms)")
            if not notes:
                notes.append("balanced feature set")
            context.pros[product["id"]] = notes
        return context


class ConsAnalyst(BaseAgent):
    def __init__(self):
        super().__init__("Cons Analyst")

    def run(self, context: AgentContext) -> AgentContext:
        for product in context.retrieved_products:
            notes = []
            if product["price"] >= 200:
                notes.append(f"premium price (${product['price']})")
            if not product["noise_cancelling"] and product["category"] in {"headphones", "earbuds"}:
                notes.append("no active noise cancelling")
            if not product["wireless"] and product["category"] in {"headphones", "keyboards", "mice"}:
                notes.append("wired-only setup")
            if 0 < product["latency_ms"] >= 80:
                notes.append(f"higher latency ({product['latency_ms']} ms)")
            if product["comfort"] < 4.2:
                notes.append("comfort may be average for long sessions")
            if not notes:
                notes.append("no major downside in this shortlist")
            context.cons[product["id"]] = notes
        return context


class RankerAgent(BaseAgent):
    def __init__(self):
        super().__init__("Ranker")

    def run(self, context: AgentContext) -> AgentContext:
        query = context.user_query.lower()
        ranked = []
        for product in context.retrieved_products:
            score = product["rating"] * 10
            score -= product["price"] / 25
            if "budget" in query or "cheap" in query or "under" in query:
                score -= product["price"] / 15
            if "noise" in query and product["noise_cancelling"]:
                score += 8
            if "wireless" in query and product["wireless"]:
                score += 5
            if "gaming" in query:
                score += max(0, 20 - product["latency_ms"]) / 2
            ranked.append(
                {
                    "product": product,
                    "score": round(score, 2),
                    "pros": context.pros.get(product["id"], []),
                    "cons": context.cons.get(product["id"], []),
                }
            )
        ranked.sort(key=lambda item: item["score"], reverse=True)
        context.ranking = ranked
        return context


class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__("CoordinatorAgent")
        self.retriever = RetrieverAgent()
        self.pros_analyst = ProsAnalyst()
        self.cons_analyst = ConsAnalyst()
        self.ranker = RankerAgent()

    def run(self, context: AgentContext) -> AgentContext:
        context = self.retriever.run(context)
        if not context.retrieved_products:
            context.final_answer = "I could not find relevant products in the catalog."
            return context
        context = self.pros_analyst.run(context)
        context = self.cons_analyst.run(context)
        context = self.ranker.run(context)
        best = context.ranking[0]
        alternatives = context.ranking[1:3]
        lines = [
            f"Top recommendation: {best['product']['name']} (${best['product']['price']}).",
            f"Pros: {', '.join(best['pros'])}.",
            f"Cons: {', '.join(best['cons'])}.",
        ]
        if alternatives:
            alt_text = "; ".join(
                f"{item['product']['name']} (${item['product']['price']})"
                for item in alternatives
            )
            lines.append(f"Other solid options: {alt_text}.")
        context.final_answer = " ".join(lines)
        return context


def run_multi_agent_system(user_query: str) -> AgentContext:
    context = AgentContext(user_query=user_query)
    coordinator = CoordinatorAgent()
    return coordinator.run(context)


def _run_self_checks() -> None:
    reset_cart()
    answer = run_shopping_agent("Find wireless headphones under 200 and add the best one to my cart")
    assert "cart total" in answer.lower()

    tmp_profile = Path("tmp_profile.json")
    if tmp_profile.exists():
        tmp_profile.unlink()
    save_profile(tmp_profile, {"preferred_category": "earbuds"})
    assert load_profile(tmp_profile)["preferred_category"] == "earbuds"
    tmp_profile.write_text("{broken", encoding="utf-8")
    assert load_profile(tmp_profile) == {}
    result = run_memory_agent(
        "I prefer wireless earbuds under 130",
        profile_path=tmp_profile,
        return_state=True,
    )
    assert result["profile"]
    follow_up = run_memory_agent(
        "What do you know about my preferences?",
        messages=result["messages"],
        profile_path=tmp_profile,
    )
    assert "saved profile" in follow_up.lower()
    context = run_multi_agent_system("Recommend wireless noise cancelling earbuds")
    assert context.ranking
    assert "Top recommendation" in context.final_answer
    tmp_profile.unlink(missing_ok=True)


if __name__ == "__main__":
    _run_self_checks()
    print("Self-checks passed.")

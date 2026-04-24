## Session Context (2026-04-24)

### Scope
- Reviewed and hardened `submission.ipynb` for final submission readiness.
- Focused on memory-agent robustness, ranking quality, and regression coverage.

### Main fixes in notebook
- Fixed profile enrichment logic in `run_memory_agent`:
  - Respect explicit user intent (brand/category/budget) before applying profile defaults.
  - Made category comparison case-insensitive.
  - Added `_mentions_budget_intent(...)` to avoid contradictory budget injection.
- Fixed profile update history flow:
  - Removed duplicated `HumanMessage` entries when multiple profile fields are updated.
  - Batched profile save after processing updates.
- Hardened extraction helpers:
  - `_extract_brand` now deterministic (sorted, longest-first).
  - Name regex in `_extract_profile_preferences` now supports Cyrillic/multi-word names.

### Ranking improvements
- Added optional `AIRankerAgent`:
  - Uses LLM prompt to choose one `product_id` from candidates.
  - Validates output and falls back deterministically to heuristic ranking on parse/error.
- Updated `CoordinatorAgent` constructor:
  - `use_ai_ranker: bool = False`
  - `ai_chat_fn=llm_chat`
  - Resolution order: explicit `ranker` -> AI ranker via flag -> default `RankerAgent`.

### Added tests (open examples in cell 5)
- `3.E`: category enrichment is case-insensitive.
- `3.F`: explicit user brand overrides stored profile brand.
- `3.G`: no duplicated `HumanMessage` during profile updates.
- `3.H`: `AIRankerAgent` selects mocked model choice.
- `3.I`: `AIRankerAgent` fallback works on invalid output.
- `3.J`: `CoordinatorAgent(use_ai_ranker=True)` path works with mocked LLM.

### Validation status
- Notebook executed end-to-end with saved outputs.
- No code-cell errors in outputs.
- Existing checks (`OK 1.*`, `OK 2.*`, `OK 3.A-3.D`) pass.
- New checks (`OK 3.E-3.J`) pass.


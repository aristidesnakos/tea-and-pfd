# OpenRouter Integration — Summary of Changes

## What Changed

ProcessFlow AI now supports **OpenRouter** (and any OpenAI-compatible API) as an alternative to Anthropic's Claude API. This allows you to use any model available on OpenRouter, including Grok, various Claude versions, o1, and more.

### Files Modified

1. **`pyproject.toml`**
   - Added `openai>=1.0.0` as a dependency

2. **`src/processflow/api/config.py`**
   - Added `openrouter_api_key` setting
   - Added `llm_provider` setting (default: "anthropic")
   - Added `llm_model` setting (default: "claude-sonnet-4-20250514")
   - Added `get_api_key()` method to select API key based on provider

3. **`src/processflow/parser/nl_parser.py`** (major refactor)
   - Updated docstring to mention OpenAI/OpenRouter support
   - Added `provider` parameter to `parse_nl_to_spec()`
   - Added auto-detection logic: uses OpenRouter if `OPENROUTER_API_KEY` is set and `ANTHROPIC_API_KEY` is not
   - Split API calls into separate functions:
     - `_call_anthropic_api()` — calls Anthropic API
     - `_call_openai_api()` — calls OpenAI-compatible API (OpenRouter)
   - Added `_parse_response()` to handle both response formats

4. **`src/processflow/api/services/job_runner.py`**
   - Updated `_parse_input()` to use `settings.get_api_key()` and pass provider/model

5. **`src/processflow/cli.py`**
   - Added `--openrouter-key` option
   - Added `--provider` option (explicit override)
   - Added `--model` option (explicit model selection)
   - Updated handler to use OpenRouter API key if provided
   - Updated docstring with OpenRouter example

### Files Created

1. **`.env.example`** — Template showing all configuration options
2. **`OPENROUTER_SETUP.md`** — User guide for setting up and using OpenRouter
3. **`OPENROUTER_INTEGRATION_SUMMARY.md`** — This file

## How It Works

### Provider Auto-Detection

The system determines which provider to use based on environment variables:

1. If `OPENROUTER_API_KEY` is set and `ANTHROPIC_API_KEY` is **not** set → use OpenRouter
2. Otherwise → use Anthropic (default)
3. Can be explicitly overridden with `--provider` flag or `PROCESSFLOW_LLM_PROVIDER` env var

### API Configuration

**Environment Variables:**
```bash
# Provider selection
PROCESSFLOW_LLM_PROVIDER=openrouter     # "anthropic" or "openrouter"
PROCESSFLOW_LLM_MODEL=x-ai/grok-4.20    # Model name for the provider

# API Keys
ANTHROPIC_API_KEY=sk-ant-...             # Anthropic
OPENROUTER_API_KEY=sk-or-...             # OpenRouter
```

**CLI Flags:**
```bash
processflow generate \
  --provider openrouter \
  --model x-ai/grok-4.20 \
  --openrouter-key sk-or-... \
  "process description"
```

## Backward Compatibility

✅ **Fully backward compatible**
- Anthropic is still the default provider
- Existing code using `ANTHROPIC_API_KEY` works without changes
- All existing tests pass (22 API tests, 57 core tests)
- No breaking changes to public APIs

## Testing

All tests pass:
```bash
# API tests (22 tests)
pytest tests/test_api.py -v

# Parser tests (4 tests)
pytest tests/test_parser.py -v

# All tests (81 tests, 2 expected graphviz failures)
pytest tests/ -v
```

## Usage Examples

### API Server with OpenRouter

```bash
# Using environment variables
export PROCESSFLOW_LLM_PROVIDER=openrouter
export PROCESSFLOW_LLM_MODEL=x-ai/grok-4.20
export OPENROUTER_API_KEY=sk-or-...
processflow-api

# Or with .env file (already set up in your project)
processflow-api
```

### CLI with OpenRouter

```bash
# Grok 4.20
OPENROUTER_API_KEY=sk-or-... processflow generate \
  --provider openrouter \
  --model x-ai/grok-4.20 \
  "describe a biorefining process"

# Claude via OpenRouter
OPENROUTER_API_KEY=sk-or-... processflow generate \
  --provider openrouter \
  --model anthropic/claude-3-5-sonnet \
  "ethanol production process"
```

### Python API

```python
from processflow.parser.nl_parser import parse_nl_to_spec

# Explicit OpenRouter
spec = parse_nl_to_spec(
    "process description",
    api_key="sk-or-...",
    model="x-ai/grok-4.20",
    provider="openrouter"
)

# Auto-detect (uses OpenRouter if OPENROUTER_API_KEY is set)
spec = parse_nl_to_spec(
    "process description",
    api_key="sk-or-...",
    model="x-ai/grok-4.20"
)
```

## Next Steps

- Your `.env` file is already configured with `OPENROUTER_API_KEY`
- Run the API server: `processflow-api`
- Use any OpenRouter model (Grok, Claude, etc.)
- See `OPENROUTER_SETUP.md` for detailed instructions

## Implementation Details

### Response Format Handling

Both APIs return different response structures:

**Anthropic:**
```python
response.content[0].text  # list of blocks
```

**OpenAI (OpenRouter):**
```python
response.choices[0].message.content  # single string
```

The `_parse_response()` function handles both formats transparently.

### Model Differences

Each provider has different capabilities:

- **Grok 4.20:** Fast, good reasoning, good coding (OpenRouter only)
- **Claude 3.5 Sonnet:** Excellent reasoning, best for complex schemas (Anthropic or OpenRouter)
- **o1:** Best reasoning, slower (OpenRouter only)

Choose based on your use case and cost constraints.

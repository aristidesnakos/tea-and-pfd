# Using OpenRouter with ProcessFlow AI

ProcessFlow AI now supports **OpenRouter** as an alternative to Anthropic's Claude API, allowing you to use any model available on OpenRouter (Grok, Claude, o1, etc.).

## Setup

### 1. Get an OpenRouter API Key

1. Visit [openrouter.io](https://openrouter.io)
2. Sign up and generate an API key
3. Add it to your `.env` file:

```bash
OPENROUTER_API_KEY=sk-or-your-key-here
```

### 2. Run the API Server with OpenRouter

Set environment variables to configure the server:

```bash
export PROCESSFLOW_LLM_PROVIDER=openrouter
export PROCESSFLOW_LLM_MODEL=x-ai/grok-4.20
export OPENROUTER_API_KEY=sk-or-your-key-here

processflow-api
```

Or use a `.env` file:

```env
PROCESSFLOW_LLM_PROVIDER=openrouter
PROCESSFLOW_LLM_MODEL=x-ai/grok-4.20
OPENROUTER_API_KEY=sk-or-...
```

Then:
```bash
processflow-api
```

### 3. Use the CLI with OpenRouter

```bash
# With Grok 4.20
OPENROUTER_API_KEY=sk-or-... processflow generate \
  --provider openrouter \
  --model x-ai/grok-4.20 \
  "corn stover to ethanol process"

# With Claude 3.5 Sonnet (via OpenRouter)
OPENROUTER_API_KEY=sk-or-... processflow generate \
  --provider openrouter \
  --model anthropic/claude-3-5-sonnet \
  "describe a biorefining process"
```

## Available Models on OpenRouter

Some popular models:

- **Grok:** `x-ai/grok-4.20`, `x-ai/grok-2-vision-1212`
- **Claude:** `anthropic/claude-3-5-sonnet`, `anthropic/claude-3-opus`
- **o1:** `openai/o1`, `openai/o1-mini`
- **Others:** `google/gemini-2.0-flash`, `meta-llama/llama-3.3-70b-instruct`, etc.

Browse all available models at: https://openrouter.ai/models

## Configuration Priority

The system auto-detects which provider to use based on environment variables:

1. If `OPENROUTER_API_KEY` is set and `ANTHROPIC_API_KEY` is **not**, use OpenRouter
2. Otherwise, use Anthropic (default)
3. You can explicitly override with `--provider` flag or `PROCESSFLOW_LLM_PROVIDER` env var

## API Configuration via Environment Variables

For the FastAPI server, use these env vars with `PROCESSFLOW_` prefix:

```bash
# Provider selection
PROCESSFLOW_LLM_PROVIDER=openrouter          # or "anthropic"
PROCESSFLOW_LLM_MODEL=x-ai/grok-4.20        # model name

# API Keys
ANTHROPIC_API_KEY=sk-ant-...                  # for Anthropic
OPENROUTER_API_KEY=sk-or-...                  # for OpenRouter
```

## Testing

```bash
# Run tests with a template (no API key needed)
pytest tests/test_api.py -v

# Full end-to-end with OpenRouter
OPENROUTER_API_KEY=sk-or-... python3 -c "
from processflow.parser.nl_parser import parse_nl_to_spec
spec = parse_nl_to_spec(
    'corn stover to ethanol',
    api_key='sk-or-...',
    model='x-ai/grok-4.20',
    provider='openrouter'
)
print(f'Process: {spec.process_name}')
"
```

## Troubleshooting

**Error: "No API key found"**
- Make sure you've set `OPENROUTER_API_KEY` or `ANTHROPIC_API_KEY` in your environment
- Check that your `.env` file is in the project root

**Error: "OpenRouter provider selected but no API key found"**
- Set `OPENROUTER_API_KEY` in your environment or `.env`
- If using CLI, pass `--provider openrouter` explicitly

**Model not found on OpenRouter**
- Check available models at https://openrouter.io/models
- Some models may be behind a waitlist or not available in your region

## Cost Considerations

OpenRouter acts as a proxy to various model providers. Pricing varies by model:

- **Grok models:** Typically cheaper than Claude
- **Claude models:** Similar to Anthropic's official pricing
- **Open-source models:** Often much cheaper

Check pricing at https://openrouter.io/models for real-time rates.

## Reverting to Anthropic

Simply unset the OpenRouter provider or set `ANTHROPIC_API_KEY`:

```bash
unset PROCESSFLOW_LLM_PROVIDER
export ANTHROPIC_API_KEY=sk-ant-...
processflow-api
```

Or explicitly in CLI:
```bash
processflow generate --api-key sk-ant-... "process description"
```

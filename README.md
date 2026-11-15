# My Local AI

A small Python desktop chat app that connects to a local Ollama model and includes basic application-level guardrails for input/output validation and prompt-injection detection.

## Features

- Tkinter-based chat UI
- Local LLM inference via Ollama
- Guardrail toggle in the app UI
- Input validation for empty messages, oversized prompts, and sensitive data patterns
- Output validation to redact common secrets and reject empty or oversized responses
- Basic prompt-injection pattern detection

## Project files

- `app.py` — main GUI application
- `guardrails.py` — system prompt and validation logic
- `ollama_test.py` — optional local testing script
- `test_model.py` — optional model-check script

## Requirements

- Python 3.9+
- Ollama installed and running locally
- A compatible model downloaded in Ollama

## Setup

1. Clone this repository.
2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install ollama
   ```

4. Pull the default model used by the app:

   ```bash
   ollama pull qwen2.5:0.5b
   ```

5. Start the Ollama service if it is not already running.

## Run the app

```bash
python app.py
```

The app launches a local chat window titled `My Local gpt` and uses the model configured in `MODEL` inside `app.py`.

## Notes

- The app is intended for local use and does not include a web backend or database.
- Guardrails are enabled by default, but can be toggled off from the UI.
- If the model is not already available locally, Ollama will need to download it before the first run.

## License

This project is provided as-is for local experimentation and learning.

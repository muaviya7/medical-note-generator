# Backend Folder Structure

## Core Files

### `model_config.py`
**Purpose**: Centralized configuration for model settings
- Model path and loading parameters
- CPU/GPU settings (threads, layers)
- Generation parameters (temperature, tokens, etc.)
- **Why**: Keeps all configuration in one place, easy to adjust performance

### `prompts.py`
**Purpose**: All LLM prompt templates
- `text_cleaner_prompt()` - Cleans transcribed medical text
- `note_generator_prompt()` - Generates structured SOAP notes
- **Why**: Separates prompt engineering from business logic

### `text_cleaner.py`
**Purpose**: Cleans raw transcribed medical text
- Removes filler words, fixes grammar
- Preserves medical information
- Uses Mistral LLM with text_cleaner_prompt
- **When to use**: First step after transcription, before note generation

### `note_generator.py`
**Purpose**: Generates structured medical notes from cleaned text
- Takes cleaned text + JSON template
- Returns filled medical note following template structure
- Uses Mistral LLM with note_generator_prompt
- **When to use**: After text cleaning, to create final structured note

### `transcription.py`
**Purpose**: Converts audio files to text
- Uses Whisper model for speech-to-text
- Handles audio file processing
- **When to use**: First step - converting audio to text

## Utility Files

### `model_download.py`
Downloads required models (Mistral, Whisper)

### `model_conversion.py`
Converts models to required formats if needed

## Supporting Files

### `main.py`
API backend (if using FastAPI/Flask)

### `config.py`
General app configuration (not model-specific)

## Directory Structure

```
backend/
├── model_config.py      # Model settings (NEW - centralized config)
├── prompts.py           # All LLM prompts
├── text_cleaner.py      # Text cleaning module
├── note_generator.py    # Note generation module
├── transcription.py     # Audio to text
├── main.py             # API server
├── config.py           # App config
├── model_download.py   # Model downloader
├── model_conversion.py # Model converter
├── models/             # Downloaded model files
│   └── mistral-7b-instruct-v0.2.Q4_K_M.gguf
└── logs/              # Log files
    ├── text_cleaner.log
    └── note_generator.log
```

## Workflow

1. **Audio → Text**: `transcription.py` (Whisper)
2. **Text → Clean Text**: `text_cleaner.py` (Mistral + text_cleaner_prompt)
3. **Clean Text → Note**: `note_generator.py` (Mistral + note_generator_prompt + template)

## Configuration

All model settings are now in `model_config.py`:
- Adjust `CPU_THREADS` based on your CPU cores
- Adjust `MAX_TOKENS_*` for output length
- Adjust `TEMPERATURE` for output consistency vs creativity

# AI Test Generator

Automatically generates pytest tests for Python code using a local LLM via Ollama.

## Requirements

- Python 3
- Ollama running locally with gemma3:4b

## Install

pip install ollama pytest

## Usage

python3 test_generator.py your_file.py

## Features

- Generates pytest tests for all functions in a file
- Auto-runs pytest after generation
- Self-corrects failing tests up to 3 attempts

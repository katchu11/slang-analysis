# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a slang term analyzer that uses two Claude models in a pipeline:
1. **Claude 3.5 Haiku** generates creative interpretations of slang acronyms (high temperature=1.0)
2. **Claude 4 Sonnet** parses these interpretations into structured JSON using tool calls (low temperature=0.1)

The project demonstrates async processing, rate limiting, and interactive data visualization.

## Key Commands

**Setup:**
```bash
uv install
export ANTHROPIC_API_KEY=your_key_here
```

**Run Web Dashboard (primary interface):**
```bash
uv run streamlit run dashboard.py
```

**Run CLI Analysis:**
```bash
uv run slang_analyzer.py YOLO --sample-size 50
```

## Architecture

### Core Components
- `slang_analyzer.py`: Core async analysis functions with rate limiting
- `dashboard.py`: Streamlit web interface with interactive Plotly charts

### Data Flow
1. Haiku generates multiple creative interpretations of a slang term
2. Sonnet parses each interpretation using structured tool calls
3. Results are aggregated and visualized with pie charts and letter breakdowns

### Rate Limiting
- 50 requests/minute with 10 concurrent connections
- Uses semaphores for concurrency control
- Progress tracking integrated with Streamlit UI

### Model Configuration
- **Haiku**: `claude-3-5-haiku-20241022` with temperature=1.0 for creativity
- **Sonnet**: `claude-sonnet-4-20250514` with temperature=0.1 for consistent parsing
- Tool calls ensure structured JSON output from Sonnet

## Development Notes

### Dependencies
- `anthropic`: Claude API client with async support
- `streamlit`: Web dashboard framework
- `plotly`: Interactive charts
- `aiohttp`: Async HTTP for rate limiting

### Key Functions
- `analyze_single_haiku()`: Single async Haiku generation
- `parse_single_sonnet()`: Single async Sonnet parsing with dynamic tool schema
- `run_analysis_with_progress()`: Streamlit-integrated progress tracking
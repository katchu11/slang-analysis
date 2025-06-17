# 🤔 WTAC - What's That Acronym, Claude?

## Inspiration

One fine Tuesday, I came across an acronym from a colleague that I didn't understand. I asked claude and it didn't know so I was curious if some other variants knew. I found out that 3.5 haiku knew once but then didn't, and then did, and it almost felt like I was picking dandelion petals. So I created this super simple repo to analyze the variance in model responses. 

Although this was a fun exercise, if you really wanted to look at this, you can tweak Haiku's generation and Sonnet's parsing functionality to work for any number of usecases like:

- Adding in knowledge connectors to see how often haiku (or any model you'd like) correctly answers the question
- If you're using Claude Code, how does usage look like (are people asking questions / writing PRDs etc.)

I think the best analogy is it's like Anthropic's [Clio](https://www.anthropic.com/research/clio), except it's Clio at home.

Also I've added [CLAUDE.md](CLAUDE.md) for the love of the game.

## High level eng components

- **Async Processing**: Fast parallel API calls with concurrency control
- **Interactive Dashboard**: Streamlit web interface with pie charts
- **Tool Call Parsing**: Structured JSON output using Claude's tool calling
- **Letter Analysis**: Drill down into what each letter could mean
- **CLI Support**: Command-line interface for batch processing

## Setup

1. **Install dependencies:**
   ```bash
   uv install
   ```

2. **Set your API key:**
   ```bash
   export ANTHROPIC_API_KEY=your_key_here
   ```

## Usage

### 🌐 Web Dashboard (Recommended)

```bash
uv run streamlit run dashboard.py
```

Then open your browser and:
1. Enter a slang term (e.g. "YNHI")
2. Choose sample size (10-200)
3. Click "Analyze" 
4. Explore interactive pie charts and letter breakdowns

### 🖥️ Command Line

```bash
uv run slang_analyzer.py YOLO --sample-size 50
```

## How It Works

1. **Generation**: Claude 3.5 Haiku generates creative interpretations (temperature=1)
2. **Parsing**: Claude 4 Sonnet parses each result into structured data using tool calls
3. **Aggregation**: Results are aggregated and visualized
4. **Interaction**: Select individual letters to see meaning distributions

## Architecture

- `slang_analyzer.py`: Core analysis functions with async support
- `dashboard.py`: Streamlit web interface with interactive charts
- Concurrency control: Max 10 concurrent requests
- Tool calls: Guaranteed structured JSON output from Claude
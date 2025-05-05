# Structured Report Generator

A simple tool that generates comprehensive, well-structured reports on any topic by researching information from the web.

## Features

- Automatic web research using Tavily API
- LLM-powered report planning and writing using Groq's llama3-70b model
- Structured report with introduction, multiple sections, and conclusion
- Markdown formatting for easy reading and further editing

## Components

- `main.py` - Main entry point that combines all functionality
- `prompts.py` - Contains all prompt templates for the LLM
- `web_search.py` - Handles web search using Tavily API
- `report_generator.py` - Generates the structured report

## Requirements

- Python 3.8+
- Tavily API key
- Groq API key for llama3-70b access

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your API keys as environment variables:

```bash
# On Linux/Mac
export TAVILY_API_KEY="your_tavily_api_key"
export GROQ_API_KEY="your_groq_api_key"

# On Windows
set TAVILY_API_KEY=your_tavily_api_key
set GROQ_API_KEY=your_groq_api_key
```

Alternatively, create a `.env` file in the project root:

```
TAVILY_API_KEY=your_tavily_api_key
GROQ_API_KEY=your_groq_api_key
```

## Usage

### Basic Usage

Run the script and enter your topic when prompted:

```bash
python main.py
```

### Command Line Arguments

You can also specify parameters via command line:

```bash
python main.py --topic "Artificial Intelligence in Healthcare" --queries 5 --temperature 0.3
```

Available options:
- `--topic`: Report topic (if not provided, will prompt for input)
- `--queries`: Number of search queries to generate (default: 3)
- `--model`: LLM model to use (default: llama3-70b-8192)
- `--temperature`: Temperature setting for LLM (default: 0.2)
- `--timeout`: Timeout in seconds for LLM API calls (default: 180)
- `--debug`: Enable debug mode with more detailed error information
- `--output-dir`: Directory to save generated reports (default: examples)

The generated report will be saved as a Markdown file named after your topic.

## Example

```bash
python main.py --topic "Quantum Computing Basics"
```

This will:
1. Research quantum computing using Tavily search
2. Generate a structured report outline
3. Write detailed content for each section 
4. Compile a final report with an introduction and conclusion
5. Save the report as `quantum_computing_basics_report.md` 
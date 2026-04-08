# Spaghetti Sniffer

> A VS Code extension that detects Python code smells using static analysis — then **roasts you about them using GPT-4o**.

Built at **HackUMass XIII** (Nov 2024).

---

## What It Does

Spaghetti Sniffer is a developer tool that brings two things together: rigorous static analysis and an LLM with a bad attitude.

On every file save, it:
1. Sends your active Python file and entire workspace to a local Flask backend
2. Runs **16 static analyzers** built on Python's `ast` module and `networkx`
3. For every issue found, calls **GPT-4o via LangChain** to generate a sarcastic, personality-driven insult
4. Renders highlighted ranges directly in the editor with AI-generated hover tooltips

The LLM doesn't just label issues — it invents distinct sarcastic personalities and randomly picks one per invocation, so every roast is different.

---

## Architecture

```
VS Code Extension (JavaScript / VS Code API)
         │
         │  POST /process
         │  { fileContent, folderContent, current_fileName }
         ▼
Flask Backend (Python, port 5000)
         │
         ├── 16 Static Analyzers (Python ast + networkx)
         │   └── returns: [{ line, tag, raw_message }]
         │
         └── GPT-4o via LangChain  ←  per-issue prompt
             └── returns: sarcastic insult string
                      │
                      ▼
         JSON response: { highlights, folderInsights }
                      │
                      ▼
VS Code decorations — highlighted ranges + hover tooltips
```

The extension sends the **entire workspace** (all `.py` files), not just the active file. This enables cross-file analyses: duplicate code detection across files, and cyclic import detection via a directed dependency graph.

---

## Detected Code Smells

| # | Smell | Detection Method |
|---|---|---|
| 1 | Unused imports | AST symbol table — imports never referenced |
| 2 | Unused variables | AST def-use chain analysis |
| 3 | Long functions (>50 lines) | AST `FunctionDef` body line span |
| 4 | Bad exception handling | Bare `except:` / catch-all `Exception` |
| 5 | Unsafe context management | File opens without `with` statement |
| 6 | Dead code | Unreachable statements after `return` / `raise` |
| 7 | High cyclomatic complexity (>5) | AST branch counting: `if`, `for`, `while`, `try`, `bool ops` |
| 8 | Hardcoded magic values | Numeric/string literals outside named constants |
| 9 | Deep nesting | Recursive AST depth traversal |
| 10 | Too many parameters | Function signature arity check |
| 11 | Bad variable names | Single-char and non-descriptive identifiers |
| 12 | Variable assigned before use | Multi-assignment without intermediate read |
| 13 | Bool literal comparisons | `== True` / `== False` / `is True` patterns |
| 14 | Debug print statements | `print()` call detection in production code |
| 15 | Unnecessary return checks | `if x: return x` redundancy pattern |
| 16 | Cross-file duplicate code | Multi-file AST similarity hashing |
| 17 | Cyclic imports | Directed import graph cycle detection (`networkx`) |

---

## LLM Integration

`lang.py` is the core of what makes this different from a standard linter.

```python
# GPT-4o via LangChain — system prompt instructs the model to:
# 1. Invent multiple distinct sarcastic personalities, each with different speaking styles
# 2. Randomly pick one per invocation
# 3. Roast the specific code issue in character, ≤25 words

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "imagine a few really sarcastic and insulting personalities. Imagine multiple "
        "that speak differently from each other and have different quirks and speaking "
        "styles. Randomly pick one of these. Using this personality, rephrase sentences "
        "in a funny, aggressive, and creatively sarcastic way. The output should sound "
        "like the random personality that you chose and should be insulting of the code "
        "issue. Keep it short and within 25 words. Issue {prompt}"
    ),
    ("human", "{prompt}"),
])

chain = prompt | llm  # gpt-4o, temperature=0
```

Each static analyzer produces a structured description of the issue (e.g., `"cyclomatic complexity too high"`, `"unused imports os"`). That description is passed directly to the chain, and the returned insult becomes the hover tooltip in the editor.

The result: instead of `"function exceeds 50 lines"`, you get something like `"Did you write this function or just copy-paste your diary? No one has time to read 80 lines of your life story."` — from a different AI persona every time.

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | GPT-4o (`gpt-4o`) |
| LLM orchestration | LangChain (`langchain-openai`, `langchain-core`) |
| Backend | Python 3 / Flask |
| Static analysis | Python `ast` module |
| Graph analysis | `networkx` (cyclic import detection) |
| VS Code extension | JavaScript / VS Code Extension API |
| HTTP client | Axios |

---

## Setup

### 1. Backend

```bash
# Install Python dependencies
pip install -r requirements.txt

# Configure your OpenAI API key
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...

# Start the Flask server (run from backend/)
cd backend
python server.py
# Listening on http://0.0.0.0:5000
```

### 2. VS Code Extension

```bash
cd extension
npm install

# Option A: dev mode — press F5 in VS Code to launch Extension Development Host
# Option B: build and install the packaged extension
npx vsce package
code --install-extension spaghetti-sniffer-0.0.1.vsix
```

---

## Usage

1. Open any Python project in VS Code
2. Open a `.py` file
3. **Save the file** — the extension fires automatically
4. Offending lines are highlighted in yellow
5. Hover over any highlight to read the AI's roast

The extension reads the entire workspace on each save to support cross-file analyses (duplicates, cyclic imports).

---

## Project Structure

```
├── README.md
├── requirements.txt
├── .env.example
│
├── backend/
│   ├── server.py                        # Flask API — orchestrates all analyzers
│   ├── lang.py                          # LLM integration — GPT-4o via LangChain
│   └── analyzers/
│       ├── __init__.py
│       ├── bad_exception_handler.py     # Bare except / catch-all detection
│       ├── long_functions.py            # Function length (>50 lines)
│       ├── unused_imports.py            # Unused imports & variables
│       ├── context_management.py        # Unsafe file opens
│       ├── dead_code.py                 # Unreachable statements
│       ├── cyclomatic_complexity.py     # Branch complexity (threshold: 5)
│       ├── hardcoded_values.py          # Magic number/string detection
│       ├── deep_nesting.py              # Recursive nesting depth
│       ├── too_many_params.py           # Function arity check
│       ├── variable_names.py            # Non-descriptive variable names
│       ├── variable_usage.py            # Assigned-before-use analysis
│       ├── bool_comparisons.py          # == True / == False patterns
│       ├── print_statements.py          # Debug print() detection
│       ├── unnecessary_return_checks.py # Redundant return patterns
│       ├── cross_file_duplicates.py     # Multi-file AST similarity hashing
│       └── cyclic_imports.py            # Import graph cycle detection (networkx)
│
├── extension/                           # VS Code extension
│   ├── extension.js                     # Extension entry point
│   ├── package.json
│   └── test/
│       └── extension.test.js
│
└── tests/
    └── fixtures/                        # Sample Python files with intentional smells
```

---

## HackUMass XIII

Built in 24 hours at HackUMass XIII (University of Massachusetts Amherst, November 2024).

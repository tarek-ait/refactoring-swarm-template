# The Refactoring Swarm

An autonomous multi-agent system that automatically detects and fixes bugs in Python code using LLM-powered analysis.

## Overview

This project implements a **LangGraph-based workflow** with three specialized agents that work together to:

1. **Audit** code for bugs using static analysis (Pylint) and test execution (Pytest)
2. **Fix** detected bugs using an LLM (Mistral AI Agent)
3. **Judge** the fixes by re-running tests to verify correctness

The system iterates up to 5 times until all tests pass or the iteration limit is reached.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py                                  │
│  - CLI entry point (--target_dir)                               │
│  - Backup management (sandbox/backup/)                          │
│  - Iteration tracking & progress display                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LangGraph Workflow                         │
│                        (src/graph.py)                           │
│                                                                 │
│    ┌──────────┐     ┌──────────┐     ┌──────────┐               │
│    │ AUDITOR  │────▶│  FIXER   │────▶│  JUDGE  │──┐           │
│    │  Agent   │     │  Agent   │     │  Agent   │   │           │
│    └──────────┘     └──────────┘     └──────────┘   │           │
│         ▲                                           │           │
│         └──────────── (if tests fail) ◀────────────┘           │
│                                                                 │
│         └──────────── (if tests pass) ──────▶ END              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Tools Layer                              │
│                     (src/tools/*.py)                            │
│                                                                 │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌───────────┐  │
│  │  Sandbox   │  │  Analyzer  │  │   Tester   │  │  File Ops │  │
│  │ (Security) │  │  (Pylint)  │  │  (Pytest)  │  │  (I/O)    │  │
│  └────────────┘  └────────────┘  └────────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## AI Configuration

### API Provider
- **Provider:** [Mistral AI](https://mistral.ai/)
- **Model:** Devstral (via Mistral Agents API)
- **Agent ID:** `ag_019b9efa2e547772b563b4378ddee0c7`

### Why Mistral AI?
- Free tier access for development and testing
- Agents API allows custom agent configurations
- Strong code understanding and generation capabilities

## 📁 Project Structure

```
refactoring-swarm-template/
├── main.py                 # CLI entry point
├── check_setup.py          # Environment validation script
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template (copy to .env)
├── .env                    # Your API keys (gitignored)
│
├── src/
│   ├── agents.py           # LLM agent definitions (Auditor, Fixer, Judge)
│   ├── graph.py            # LangGraph workflow definition
│   ├── state.py            # State schema (SwarmState TypedDict)
│   │
│   ├── tools/              # Reusable tools for agents
│   │   ├── __init__.py     # Public API exports
│   │   ├── sandbox.py      # Security & path validation
│   │   ├── file_ops.py     # Safe file I/O operations
│   │   ├── analyzer.py     # Pylint integration
│   │   ├── tester.py       # Pytest integration
│   │   ├── parser.py       # AST-based code parsing
│   │   ├── function_fixer.py # Code transformation utilities
│   │   └── exceptions.py   # Custom exception types
│   │
│   └── utils/
│       └── logger.py       # Experiment logging (JSON format)
│
├── sandbox/                # Target directory for buggy code
│   ├── backup/             # Automatic backups before fixes
│   ├── bad_calc.py         # Example buggy code
│   ├── test_bad_calc.py    # Tests defining correct behavior
│   ├── bad_pricing.py      # Complex business logic bugs
│   ├── test_bad_pricing.py
│   ├── bad_inventory.py    # Inventory management bugs
│   └── test_bad_inventory.py
│
└── logs/
    └── experiment_data.json # Agent action logs
```

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd refactoring-swarm-template
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# The .env.example contains the exact API configuration used in development:
# MISTRAL_API_KEY=<api-key>
# MISTRAL_MODEL=ag_019b9efa2e547772b563b4378ddee0c7
```

### 3. Verify Setup

```bash
python check_setup.py
```

Expected output:
```
🔍 Démarrage du 'Sanity Check'...

✅ Python Version: 3.10
✅ Fichier .env détecté.
✅ Clé API présente (format non vérifié).
✅ Dossier logs/ créé.

🚀 TOUT EST PRÊT ! Vous pouvez commencer.
```

### 4. Run the Refactoring Swarm

```bash
python main.py --target_dir "./sandbox"
```

Expected output:
```
LAUNCHING: DEMARRAGE SUR : ./sandbox

ON-GOING: Processing Pair: ./sandbox/bad_calc.py + ./sandbox/test_bad_calc.py
  Backup created: ./sandbox/backup/bad_calc.py.20260128_200000.bak
  ↳ Iteration 1/5
    Fixer modified code
  ↳ Iteration 2/5
  Tests passed!
  Written fixed code to ./sandbox/bad_calc.py
SUCCESS: Finished processing ./sandbox/bad_calc.py

MISSION_COMPLETE
```

### 5. Verify Fixes

```bash
pytest sandbox/test_bad_calc.py -v
```

## Workflow Details

### Agent Responsibilities

| Agent | Role | Tools Used |
|-------|------|------------|
| **Auditor** | Analyzes code for bugs and runs tests | Pylint, Pytest |
| **Fixer** | Generates fixed code using LLM | Mistral Agents API |
| **Judge** | Validates fixes by running tests | Pytest, Pylint |

### State Schema

```python
class SwarmState(TypedDict):
    target_file: str        # Path to the file being fixed
    test_file: str          # Path to the corresponding test file
    code_content: str       # Current content of the code
    pylint_report: str      # Output from the auditor agent
    test_report: str        # Output from the judge agent
    iteration: int          # Loop counter (max: 5)
    is_success: bool        # Flag to stop the swarm
    task_description: str   # Description of the task
```

### Iteration Flow

1. **Auditor** runs Pylint and Pytest on current code
2. **Fixer** sends code + test failures to Mistral Agent for fixes
3. **Judge** writes fixed code to file and re-runs tests
4. If tests pass → **END**
5. If tests fail and iteration < 5 → Go to step 1
6. If iteration >= 5 → **END** (max iterations reached)

## Logging

All agent actions are logged to `logs/experiment_data.json`:

```json
{
    "timestamp": "2026-01-28T19:42:00",
    "agent_name": "Fixer",
    "model_used": "ag_019b9efa2e547772b563b4378ddee0c7",
    "action": "FIX",
    "details": {
        "input_prompt": "Fixing code (1234 chars) with 567 chars of tests",
        "output_response": "Generated fixed code (1289 chars)"
    },
    "status": "SUCCESS"
}
```

## Security Features

- **Sandbox isolation:** All file operations are restricted to the target directory
- **Path validation:** Prevents directory traversal attacks (`../`)
- **Atomic writes:** Uses temp file + rename to prevent corruption
- **Automatic backups:** Original files are backed up before modification

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `langgraph` | 0.0.25 | Workflow orchestration |
| `mistralai` | 1.10.0 | LLM API client |
| `pylint` | 3.0.3 | Static code analysis |
| `pytest` | 7.4.4 | Test execution |
| `python-dotenv` | 1.0.1 | Environment configuration |

## Test Files Included

### bad_calc.py (8 functions)
- Off-by-one errors
- Wrong comparison operators
- Mutable default arguments
- Division errors
- Early returns
- Incorrect initialization

### bad_pricing.py (1 function)
- Complex business logic
- Discount calculation order
- Tax and shipping rules

### bad_inventory.py (8 functions)
- Stock value calculation
- Threshold comparisons
- SKU lookups
- Quantity updates
- Inventory merging

## Configuration Options

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MISTRAL_API_KEY` | Your Mistral AI API key | `IZrnXBp...` |
| `MISTRAL_MODEL` | Agent ID or model name | `ag_019b9efa...` |

### Runtime Options

```bash
python main.py --target_dir "./path/to/buggy/code"
```

## Creating Your Own Test Cases

1. Create a buggy Python file: `sandbox/bad_example.py`
2. Create tests that define correct behavior: `sandbox/test_bad_example.py`
3. Run the swarm: `python main.py --target_dir "./sandbox"`

The agent will:
- Detect the file pair automatically
- Create a backup in `sandbox/backup/`
- Attempt to fix bugs until tests pass

## Troubleshooting

### "Invalid model" error
Ensure `MISTRAL_MODEL` in `.env` is a valid Agent ID (starts with `ag_`) or model name.

### "Sandbox not initialized" error
The sandbox must be initialized before any file operations. This is handled automatically in `main.py`.

### Tests still failing after 5 iterations
Some bugs may be too complex for the LLM to fix automatically. Check `logs/experiment_data.json` for details on what was attempted.

### No changes made to file
The fixer may be returning the same code. Check the logs for "Agent returned empty or invalid code" errors.

## Authors

- [Rayan Derradji - Lead Dev](https://github.com/Rennsen)
- [Anes Abdelhak Hadim - Data Officer](https://github.com/Anes-Hadim)
- [Tarek Ait Ahmed - Toolsmith](https://github.com/tarek-ait)
- [Abdellah Zeghmar - Prompt Engineer](https://github.com/Abdellahz0)

# Refactoring Swarm Template

A multi-agent system for automated code refactoring and bug fixing using LLM-powered agents.

## Prerequisites

- Python 3.10 or higher (3.11+ recommended)
- Git
- A Mistral AI API key and Agent ID

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/tarek-ait/refactoring-swarm-template.git
cd refactoring-swarm-template
```

### 2. Create a Virtual Environment

```bash
python3 -m venv .venv
```

### 3. Activate the Virtual Environment

**Linux/macOS:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```bash
touch .env
```

Add your API credentials:

```env
# Mistral API Key
MISTRAL_API_KEY=your-mistral-api-key-here

# The specific Agent ID
MISTRAL_AGENT_ID=your-mistral-agent-id-here
```

> ⚠️ **Important:** Never commit your `.env` file. It's already in `.gitignore`.

### 6. Verify Setup

Check that Python is using the virtual environment:

```bash
which python   # Should show .venv/bin/python
python -V      # Should show Python 3.10+
```

Verify dependencies are installed:

```bash
pip list
```

## Running the Project

### 1. Prepare Your Target Code

Place the buggy code and corresponding test files in the `sandbox/` folder:

```
sandbox/
├── bad_code.py        # The code to refactor
└── test_bad_code.py   # The test file (must be named test_<filename>.py)
```

### 2. Run the Main Script

```bash
python main.py --target_dir "./sandbox"
```

### 3. Expected Output

```
🚀 DEMARRAGE SUR : ./sandbox
🔄 Processing Pair: ./sandbox/bad_code.py + ./sandbox/test_bad_code.py
✅ Finished processing ./sandbox/bad_code.py
✅ MISSION_COMPLETE
```

## Checking Logs

Experiment data is logged to `logs/experiment_data.json`:

```bash
cat logs/experiment_data.json
```

Or use `jq` for formatted output:

```bash
jq . logs/experiment_data.json
```

## Committing and Pushing Results

### 1. Check Status

```bash
git status
```

### 2. Add the Experiment Log

```bash
git add logs/experiment_data.json
```

### 3. Commit Changes

```bash
git commit -m "Add experiment results"
```

### 4. Push to Remote

```bash
git push origin your-branch-name
```

## Troubleshooting

### "Missing MISTRAL_API_KEY or MISTRAL_AGENT_ID"

- Ensure `.env` file exists in the project root
- Verify the keys are correctly set (no extra spaces)
- Make sure `load_dotenv()` is called before imports in `main.py`

### "No test found for file. Skipping."

- Test files must follow the naming convention: `test_<filename>.py`
- Both the code file and test file must be in the same directory

### Python version warning

If you see a `FutureWarning` about Python 3.10:

```bash
# Install Python 3.11+ and recreate the venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Project Structure

```
refactoring-swarm-template/
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── .env                    # API keys (not committed)
├── .gitignore
├── sandbox/                # Target code directory
├── logs/
│   └── experiment_data.json  # Experiment results
└── src/
    ├── agents.py           # LLM agent definitions
    ├── graph.py            # Agent workflow graph
    ├── tools.py            # Utility functions
    └── utils/
        └── logger.py       # Logging utilities
```
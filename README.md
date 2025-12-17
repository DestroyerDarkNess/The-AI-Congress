# The-AI-Congress
The-AI-Congress is an agent-based planning system with a parliamentary flow: a President drafts a plan, Deputies with distinct expertise vote on its quality, and once a plan reaches consensus the agent executes it step by step.

## Capabilities
- Generate structured plans for any user objective by prompting an LLM from the `President` role.
- Validate, critique, and request improvements via specialized `Deputy` personas covering architecture, security, and product priorities.
- Execute approved plans by invoking tools that explore directories, read files, write updates, and run shell commands, following the LLM’s JSON-based tool invocation rules.
- Provide a Rich-powered console experience for status, panels, and markdown rendering throughout the interaction.
- Support configurable LLM endpoints through the `OpenAILikeProvider`.

## Requirements
- Python 3.10+
- `.env` file with an `OPENAI_API_KEY` pointing to your provider.
- Dependencies installed from `requirements.txt`.

## Setup
1. Clone the repository and enter the project directory.
2. Create and activate a virtual environment:
   ```sh
   python -m venv .venv
   .venv\\Scripts\\activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

## Configuration
Copy `.env.example` to `.env` and provide a valid API key:
```
OPENAI_API_KEY=sk-...
```
`main.py` loads `.env` automatically. By default, `OpenAILikeProvider` targets `https://unifiedai.runasp.net/v1`—adjust the `base_url` argument there if another endpoint is required.

## Usage
1. Ensure the virtual environment is active and dependencies installed.
2. Run the interface:
   ```sh
   python main.py
   ```
3. Enter your objective in the prompt. The Parliament reviews and approves a plan before the agent executes it, ensuring tools are used only via the prescribed JSON blocks.

## Project Structure
- `main.py`: boots the console interface, configures the `OpenAILikeProvider`, and wires the Parliament and Agent together.
- `agent_system/`: all agent logic and supporting modules.
  - `core.py`: base `Agent` implementation with tool orchestration.
  - `tools/`: `list_directory`, `read_file`, `modify_file`, and `system_shell` tools reachable by the agent.
  - `planning/`: `President`, `Deputy`, and `Parliament` classes forming the review workflow.
- `requirements.txt`: Python dependencies.
- `.gitignore`, `.env`, `.env.example`: environment and ignore management.

## Parliamentary Flow
1. The `President` produces an initial Markdown plan from the user objective and available tool descriptions.
2. Each `Deputy` reviews the plan, votes yes/no, and adds a concise note.
3. If all deputies approve, the plan is final. Otherwise the `President` refines it, and up to three voting rounds occur.
4. When consensus is reached or the maximum rounds pass, the agent executes the approved plan, calling tools via structured JSON responses.

## Contributing
1. Fork the repository and create a descriptive branch.
2. Add or update tests when changing functionality.
3. Submit a pull request with a summary of changes and references to modified modules.

## License
See [LICENSE](LICENSE) for the project license.

# GEMINI.md - Personal AI Employee Context

## Project Overview
The **Personal AI Employee** is a multi-tier intelligent automation system designed to manage personal and business workflows. It uses a "Human-in-the-Loop" architecture where AI agents (like Claude Code or Gemini) perform tasks based on instructions found in Markdown files, while an Obsidian vault serves as both the database and the user interface.

- **Current Version:** Silver Tier (v2.0)
- **Core Purpose:** Automate email processing, social media engagement (LinkedIn), and general task execution.
- **Architecture:**
    - **Watchers:** Background processes monitor the filesystem, Gmail, and LinkedIn for new triggers.
    - **Orchestrator:** A central manager that coordinates watchers and triggers the AI processing engine.
    - **Skills Framework:** Modular Python scripts (`src/orchestrator/skills/`) that perform specific API-driven actions.
    - **State Management:** Task progression is handled by moving Markdown files through a directory hierarchy (`Inbox` -> `Needs_Action` -> `Pending_Approval` -> `Approved` -> `Done`).

## Technologies
- **Language:** Python 3.10+
- **AI Engine:** Claude Code CLI (primary reasoning engine)
- **UI/Storage:** Obsidian (Markdown-based vault)
- **APIs:** Gmail API, LinkedIn REST API
- **Key Libraries:** `watchdog` (monitoring), `psutil` (process management), `google-api-python-client`.

## Building and Running

### Setup
The project uses a virtual environment and a comprehensive setup script:
```bash
./setup.sh
```
This script initializes the `venv`, installs dependencies, creates the `ai_employee_vault` structure, and guides through API configuration.

### Running the System
The system is designed to run as a suite of background watchers managed by a `watcher_manager`.

- **Start All Watchers:** `./start.sh`
- **Stop All Watchers:** `./stop.sh`
- **Check Status:** `python -m src.orchestrator.watcher_manager ./ai_employee_vault status`
- **Manual Execution (Individual Watchers):**
    - Filesystem: `python -m src.watchers.run_filesystem_watcher ./ai_employee_vault`
    - Gmail: `python -m src.watchers.run_gmail_watcher ./ai_employee_vault`
    - LinkedIn: `python -m src.watchers.run_linkedin_watcher ./ai_employee_vault`

### Testing
- **LinkedIn Integration:** `python -m src.orchestrator.skills.post_linkedin '{"action": "create_post", "content": "Test post"}'`
- **General Skills:** Skills can often be run directly via Python for testing their specific logic.

## Development Conventions

### Agent Skills
- All new automated capabilities should be implemented as modular scripts in `src/orchestrator/skills/`.
- Skills should inherit from `BaseSkill` (if defined) or follow the established pattern of accepting JSON-like inputs and updating the vault.

### Human-in-the-Loop (HITL)
- **Mandatory Approval:** Social media posts, financial transactions, and deletions *must* be routed through `Pending_Approval`.
- **Workflow:** AI creates a request in `Pending_Approval` -> User moves file to `Approved` -> Watcher detects and triggers execution.

### Coding Style & Standards
- **Logging:** Use the established logging pattern; logs should go to `ai_employee_vault/Logs/`.
- **State Files:** Respect the `.state/` directory for lock files and persistence.
- **Handbook Adherence:** Always check `ai_employee_vault/Company_Handbook.md` for rules of engagement and decision-making logic.

## Key Directories
- `src/orchestrator/`: Main logic for process management and task coordination.
- `src/watchers/`: Entry points for various data source monitors.
- `src/orchestrator/skills/`: The "tools" available to the AI agent.
- `ai_employee_vault/`: The live environment where tasks are processed and state is visualized.
- `credentials/`: Storage for API tokens and OAuth secrets (Keep Secure).

## Operational Workflow
1. **Trigger:** A watcher detects a new item (file in Inbox, new Email, LinkedIn calendar event).
2. **Detection:** The orchestrator/watcher creates a task file in `Needs_Action`.
3. **Execution:** The AI engine is triggered to process the task using available **Skills**.
4. **Completion:** The task file is moved to `Done`, and the `Dashboard.md` is updated.

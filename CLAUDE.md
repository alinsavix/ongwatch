# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ongwatch is a stream event monitoring system that watches for events from multiple streaming backends (Twitch, StreamElements, Streamlabs) and publishes them to a message bus (planned MQTT). The goal is to allow multiple bots and tools to share stream events without each needing to individually authenticate and manage connections to streaming services.

The project is in active development. Current status: backend connections are functional, MQTT integration is planned but not yet implemented.

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Install dev dependencies
uv sync --all-extras
```

### Running the Application
```bash
# Run with default environment (test)
./ongwatch.py --credentials-file credentials.toml

# Run with specific environment
./ongwatch.py --env prod

# Enable specific backend
./ongwatch.py --enable-backend twitch

# Disable specific backend
./ongwatch.py --disable-backend streamlabs

# Enable debug logging for a backend
./ongwatch.py --debug-backend twitch

# Run authentication flow for a backend
./ongwatch.py --auth twitch --env test
```

### Linting and Type Checking
```bash
# Run mypy for type checking
uv run mypy .

# Run flake8 for linting
uv run flake8
```

## Architecture

### Backend Plugin System

The application uses a pluggable backend architecture in `_ongwatch/backends/`. Each backend is a Python module that must implement:

- `start(args, creds, logger)` - Async coroutine that connects to the backend and runs indefinitely
- `auth(args, creds, logger)` - (Optional) Async coroutine for interactive authentication flow

Backends are loaded dynamically via `backends.get_backend(name)` which uses `importlib.import_module()`.

Available backends are listed in `BACKEND_LIST` in `_ongwatch/backends/__init__.py`.

### Main Event Loop

The main application (`ongwatch.py`) runs an asyncio event loop that:

1. Loads credentials from a TOML file for each enabled backend
2. Creates an asyncio task for each backend's `start()` function
3. Waits for either a shutdown signal or any backend task to complete
4. On shutdown, cancels all backend tasks gracefully

Signal handling is platform-aware (different for Windows vs Unix).

### Backend Implementations

**Twitch Backend** (`_ongwatch/backends/twitch.py`):
- Uses the `twitch.py` library (EventSub websocket connections)
- Implements custom `OngWatch_Twitch` client subclassing `twitch.Client`
- Handles events via `on_*` methods (e.g., `on_stream_online`, `on_chat_message`, `on_bits_use`)
- Special handling for Nightbot messages to detect song requests (`!sr`) and raffle winners
- Stores user tokens in JSON files (refreshable OAuth tokens)

**StreamElements Backend** (`_ongwatch/backends/streamelements.py`):
- Uses python-socketio for real-time connection
- Implements `OngWatch_SE` namespace handler
- Authenticates with API key or JWT
- Currently handles tip events

**Streamlabs Backend** (`_ongwatch/backends/streamlabs.py`):
- Similar socket.io based implementation

### Credentials Management

Credentials are stored in `credentials.toml` with structure:
```toml
[backend_name.environment_name]
key = "value"
```

The `get_credentials()` function in `_ongwatch/util.py` loads credentials for a specific backend and environment combination.

Token files for OAuth backends (like Twitch) are stored separately as JSON files named `{backend}_user_token.{environment}.json`.

### Output Format

Currently outputs to stdout/stderr in a tab-separated format via utility functions in `_ongwatch/util.py`:
- `printsupport()` - For support events (tips, bits, subs, raids)
- `printextra()` - For extra info like song requests
- `out()` - For general events

Timestamps are formatted in US/Eastern timezone.

## Code Style and Conventions

### Python Style
- Python 3.13+ required
- Use snake_case for variables, functions, and filenames
- Use PascalCase for classes
- Follow PEP 8 formatting
- Use type hints extensively (strict mypy configuration enabled)
- Max line length: 96 characters (see autopep8 config in pyproject.toml)
- Use double quotes for strings by default, single quotes for enum-like strings
- Comments must be complete sentences starting with capital letter
- Use early returns to avoid deep nesting
- Handle errors at the beginning of functions

### Logging
- Use the standard `logging` module
- Default log level is INFO
- Enable DEBUG per-backend with `--debug-backend <name>`
- Each backend gets its own logger via `logging.getLogger(backend_name)`

### Testing
- Use pytest for testing (dev dependency included)
- Currently no test suite exists

## Git Conventions

### Commit Messages
- Use prefixes like `twitch:`, `backend:`, `docs:`, `meta:` to indicate which part of the project
- Prefix can be omitted on small changes
- Subject line should complete: "if this change were committed, it would _____________"

Example: `twitch: fix nightbot messages when they're notifications`

## Important Notes

- The actual message bus (MQTT) functionality is not yet implemented
- `_ongwatch/_version.py` is auto-generated by hatch-vcs from git tags
- The project uses uv for dependency management (not pip or poetry)
- Token files and credentials.toml should never be committed (already in .gitignore)

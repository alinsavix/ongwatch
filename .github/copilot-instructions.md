# GitHub Copilot Custom Instructions for Python Project

## Dependency Management

- This Python project uses **uv** to manage dependencies.
- Dependencies are recorded in `pyproject.toml`, not `requirements.txt`.
- Always follow this when generating or modifying dependency code.

## Testing

- Use **pytest** as the testing framework.
- Write clear and maintainable test functions.
- Use fixtures for setup and teardown.
- Create tests only if the project already has tests


## Git Commit Message Conventions

- For the subject of a git commit:
  - Use a prefix that indicates which part of the project the commit is for. Some example prefixes (you are not restricted to this list, they are just examples):
    - `backend:` for backend code
    - `docs:` for documentation
    - `lufsplot:` for a sub-project named "lufsplot"
- The prefix is not strictly required, and can be omitted on small projects
- The descriptive part of the subject for a git commit should be a sentence fragment that completes the sentence "if this change were committed, it would _____________"


## Python Code Style - Naming

- Use snake_case for functions and variables.
- Use CamelCase for classes.
- Constants in UPPER_SNAKE_CASE.
- Use descriptive and unambiguous names.
- Avoid abbreviations unless they are widely understood.
- Use pronounceable names and maintain consistent naming conventions.


## Python Code Style - Formatting

- Follow PEP 8 guidelines.
- Use 4 spaces for indentation; no tabs.
- Normally keep line lengths below 80 characters
- If needed for clarity, you can use line lengths up to 132 characters.
- Two blank lines before top-level functions/classes.
- Use double quotes for most strings, but single quotes for strings that are basically enums (e.g. can only be set to one of a small number of predetermined values)


## Python Code Style - Comments and Documentation

- Assume your audience is an experienced developer and does not need every line of code explained.
- Don't add docstrings unless requested.
- If a docstring already exists for a function you are modifying, update it to remain accurate.
- Comments must be complete sentences starting with a capital letter.
- Limit comment lines to 80 characters.
- Use block comments indented to code level, starting with `#`.
- Separate paragraphs in block comments with a single `#` line.
- Use inline comments sparingly, separated by two spaces, starting with `#`.
- Avoid obvious comments; explain *why* not *what*.
- Write comments in English.
- **Ensure comments are updated promptly to reflect any code changes.**


## Python Code Style - General Practices

- Write code that is easy to read and maintain; prioritize clarity over cleverness
- Use type annotations, but don't spend time trying to fix existing type errors
- Keep functions focused and simple; extract common logic into functions or classes, but ask before starting a major refactor
- Avoid deep nesting; use early returns to reduce complexity
- Prefer exceptions over return codes for error handling, where it makes sense
- Handle exceptions gracefully with try-except blocks; avoid bare excepts
- Use context managers (`with` statement) for resource management
- Never include passwords or secrets in code.


## Python Code Style - Libraries and Modules

- Prefer standard library modules where possible
- We prefer the following modules for specific tasks, unless there is good reason to use an alternative, or the project is already using a different library:
  - For argument handling, use `argparse`
  - For all filesystem and path related things, use `pathlib`
  - For database interactions, use `peewee`
  - For logging, use the standard `logging` module


## Logging

- Configure loggers with appropriate log levels (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
- The default log level should be `INFO`, with an available command line option to enable `DEBUG`
- Avoid using print statements for logging.
- Include contextual information in log messages to aid debugging.
- Follow consistent log message formatting.

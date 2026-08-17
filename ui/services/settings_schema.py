# ui/services/settings_schema.py
"""
Shared settings vocabulary and validation.

FIELDS is the single source of truth for what a "setting" is: the dotted
name a person types (in the TUI settings screen's `set`/`get`/`reset`
commands, or the `clice set`/`clice get`/`clice reset` CLI subcommands),
the Config attribute it actually maps to, and a human description.

cast_and_validate() is the one place raw string input gets turned into a
real typed value and sanity-checked, so the TUI and the CLI can never
drift into accepting different things for the same key.
"""
import re

from ui.services.config import Config

FIELDS = [
    ("resources.memory",          "challenge_mem_limit",    "Max memory allocation (e.g. 512m, 1g)"),
    ("resources.cpu_cores",       "challenge_cpu_cores",    "CPU cores allocated per challenge"),
    ("resources.checker_timeout", "checker_timeout",        "Checker script timeout (seconds)"),
    ("resources.docker_timeout",  "docker_timeout",         "Docker container startup timeout (seconds)"),
    ("behaviour.network",         "network_enabled",        "Allow network access inside challenges"),
    ("behaviour.auto_cleanup",    "auto_cleanup",           "Auto-remove containers after a session"),
    ("ai.model",                  "openrouter_model",       "AI model used for verdict feedback"),
    ("ai.api_key",                "openrouter_api_key",     "OpenRouter API key (masked - use `get` to reveal)"),
    ("ai.max_tokens",             "openrouter_max_tokens",  "Max length of AI feedback responses"),
]

KEY_TO_ATTR = {key: attr for key, attr, _ in FIELDS}
ATTR_TO_KEY = {attr: key for key, attr, _ in FIELDS}

BOOL_TRUE = {"1", "true", "yes", "on", "enabled"}
BOOL_FALSE = {"0", "false", "no", "off", "disabled"}

# Sentinel meaning "this attribute had no override at all" (i.e. it was
# sitting at its .env default) - distinct from any real stored value.
UNSET = object()


def cast_and_validate(attr: str, raw_value: str):
    """Turn a raw string (from a CLI arg or a TUI Input) into the real
    typed value for this Config attribute, raising ValueError with a
    human-readable message if it doesn't pass sanity checks."""
    _, cast = Config._SCHEMA[attr]
    raw_value = raw_value.strip()

    if not raw_value:
        raise ValueError("value can't be empty")

    if cast is bool:
        low = raw_value.lower()
        if low in BOOL_TRUE:
            return True
        if low in BOOL_FALSE:
            return False
        raise ValueError("expected on/off, true/false, or yes/no")

    if cast is int:
        try:
            value = int(raw_value)
        except ValueError:
            raise ValueError("expected a whole number")
    elif cast is float:
        try:
            value = float(raw_value)
        except ValueError:
            raise ValueError("expected a number")
    else:
        value = raw_value

    # Field-specific sanity ranges - reject nonsense before it ever
    # reaches Config.save() / the containers that read these values.
    if attr == "challenge_cpu_cores" and value <= 0:
        raise ValueError("must be greater than 0")
    if attr in ("checker_timeout", "docker_timeout") and value <= 0:
        raise ValueError("must be greater than 0 seconds")
    if attr == "openrouter_max_tokens" and not (50 <= value <= 4000):
        raise ValueError("must be between 50 and 4000")
    if attr == "challenge_mem_limit":
        if not re.fullmatch(r"\d+[mMgG]", value):
            raise ValueError("expected a format like 512m or 1g")

    return value


def display_value(attr: str, value) -> str:
    """Render a value for display, masking the API key unless explicitly
    revealed via `get`. Matches SettingsScreen._display_value exactly."""
    if attr == "openrouter_api_key":
        if not value:
            return "(not set)"
        return f"***{value[-4:]}" if len(value) >= 4 else "***"
    if isinstance(value, bool):
        return "ENABLED" if value else "DISABLED"
    return str(value)
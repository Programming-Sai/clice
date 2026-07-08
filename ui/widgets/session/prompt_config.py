# ui/widgets/session/prompt_config.py

# Default prompt (used as fallback)
DEFAULT_PROMPT = "user@clice:/mnt/hello/workspace~$ "

# Current prompt (updated dynamically)
_current_prompt = DEFAULT_PROMPT

def get_prompt() -> str:
    """Get the current prompt text."""
    return _current_prompt

def set_prompt(prompt: str) -> None:
    """Update the current prompt."""
    global _current_prompt
    _current_prompt = prompt

def get_prompt_len() -> int:
    """Get the length of the current prompt."""
    return len(_current_prompt)

def get_prompt_pad() -> str:
    """Get padding string matching the current prompt length."""
    return " " * get_prompt_len()

# Backward compatibility
PROMPT_TEXT = DEFAULT_PROMPT
PROMPT_LEN = len(PROMPT_TEXT)
PROMPT_PAD = " " * PROMPT_LEN
# ui/services/config.py
from pathlib import Path
import json
import os
from dotenv import load_dotenv

class Config:
    """Configuration with two layers:

      1. .env - shipped/factory defaults, checked into the project (or a
         local override a developer drops in). Read-only from the app's
         perspective; never written back to.
      2. ~/.clice/settings.json - created at runtime, holds only the
         settings a user has actually changed via the settings screen (or
         Config.save()). Loaded on top of the .env-derived defaults, so a
         fresh install with no settings.json behaves purely off .env, and
         changing a setting never touches the shipped .env at all.
    """

    # attribute name -> (env var name, type)
    # Single source of truth for both env parsing and settings.json
    # save()/load() - add a setting here once and both paths pick it up.
    _SCHEMA = {
        "challenge_mem_limit": ("CLICE_CHALLENGE_MEM_LIMIT", str),
        "challenge_cpu_cores": ("CLICE_CHALLENGE_CPU_CORES", float),
        "checker_timeout":     ("CLICE_CHECKER_TIMEOUT", int),
        "docker_timeout":      ("CLICE_DOCKER_TIMEOUT", int),
        "network_enabled":     ("CLICE_NETWORK_ENABLED", bool),
        "auto_cleanup":        ("CLICE_AUTO_CLEANUP", bool),
        "openrouter_api_key":  ("OPENROUTER_API_KEY", str),
        "openrouter_model":    ("OPENROUTER_MODEL", str),
        "openrouter_max_tokens": ("OPENROUTER_MAX_TOKENS", int),
    }

    def __init__(self):
        # Look for .env in the app directory
        possible_paths = [
            Path.cwd() / ".env",
            Path(__file__).parent.parent.parent / ".env",
            Path.home() / ".clice" / ".env",
        ]

        self.env_path = None
        for env_path in possible_paths:
            if env_path.exists():
                load_dotenv(env_path)
                self.env_path = env_path
                break

        # Registry settings
        self.registry_url = os.getenv(
            "CLICE_REGISTRY_URL",
            "https://raw.githubusercontent.com/programming-sai/clice-challenges/registry/registry.json"
        )
        self.registry_hash_url = os.getenv(
            "CLICE_REGISTRY_HASH_URL",
            "https://raw.githubusercontent.com/programming-sai/clice-challenges/registry/registry.hash"
        )

        # Cache/logs directories - expand ~ in env values
        cache_env = os.getenv("CLICE_CACHE_DIR", str(Path.home() / ".clice" / "cache"))
        logs_env = os.getenv("CLICE_LOGS_DIR", str(Path.home() / ".clice" / "runs"))
        self.cache_dir = Path(os.path.expanduser(cache_env))
        self.logs_dir = Path(os.path.expanduser(logs_env))

        # Where user overrides live - a sibling of cache_dir, always under
        # ~/.clice regardless of CLICE_CACHE_DIR, so it's predictable.
        self.settings_path = Path.home() / ".clice" / "settings.json"

        # ── Settings-screen-backed fields: seed from .env defaults first ──
        self.challenge_mem_limit = os.getenv("CLICE_CHALLENGE_MEM_LIMIT", "512m")
        self.challenge_cpu_cores = float(os.getenv("CLICE_CHALLENGE_CPU_CORES", "1.0"))
        self.checker_timeout = int(os.getenv("CLICE_CHECKER_TIMEOUT", "20"))
        self.docker_timeout = int(os.getenv("CLICE_DOCKER_TIMEOUT", "30"))
        self.network_enabled = self._to_bool(os.getenv("CLICE_NETWORK_ENABLED", "true"))
        self.auto_cleanup = self._to_bool(os.getenv("CLICE_AUTO_CLEANUP", "true"))
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324:free")
        self.openrouter_max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "800"))

        # Snapshot of the .env-derived (factory) values, captured before user
        # overrides are layered on - this is what the settings screen shows
        # in its "DEFAULT" column and what `reset` reverts a field to.
        self._env_defaults = {attr: getattr(self, attr) for attr in self._SCHEMA}

        # ── Layer user overrides from settings.json on top, if present ──
        self._apply_settings_file()

    @staticmethod
    def _to_bool(value) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("1", "true", "yes", "on")

    def _apply_settings_file(self):
        if not self.settings_path.exists():
            return
        try:
            overrides = json.loads(self.settings_path.read_text())
        except (json.JSONDecodeError, OSError):
            # Corrupt or unreadable settings file - fall back to .env
            # defaults rather than crashing the whole app on startup.
            return

        for attr, value in overrides.items():
            if attr not in self._SCHEMA:
                continue  # ignore unknown/stale keys rather than erroring
            _, cast = self._SCHEMA[attr]
            try:
                setattr(self, attr, cast(value) if cast is not bool else self._to_bool(value))
            except (TypeError, ValueError):
                continue  # ignore a single bad value rather than failing startup

    @property
    def challenge_nano_cpus(self) -> int:
        """CPU core count converted to docker-py's nano_cpus unit."""
        return int(self.challenge_cpu_cores * 1_000_000_000)

    def ensure_config(self):
        """Create default .env if it doesn't exist."""
        env_path = Path(__file__).parent.parent / ".env"
        if not env_path.exists():
            env_path.write_text("""
    CLICE_REGISTRY_URL=https://raw.githubusercontent.com/programming-sai/clice-challenges/registry/registry.json
    CLICE_REGISTRY_HASH_URL=https://raw.githubusercontent.com/programming-sai/clice-challenges/registry/registry.hash
    CLICE_CACHE_DIR=~/.clice/cache
    CLICE_LOGS_DIR=./assets
    CLICE_DOCKER_TIMEOUT=30
    CLICE_CHALLENGE_MEM_LIMIT=512m
    CLICE_CHALLENGE_CPU_CORES=1.0
    CLICE_CHECKER_TIMEOUT=20
    CLICE_NETWORK_ENABLED=true
    CLICE_AUTO_CLEANUP=true
    OPENROUTER_API_KEY=
    OPENROUTER_MODEL=
    OPENROUTER_MAX_TOKENS=800
    """)

    def save(self, **updates):
        """
        Persist one or more settings as user overrides in
        ~/.clice/settings.json (never touches .env) and update this
        instance in place.

        Example: config.save(challenge_mem_limit="1g", network_enabled=False)
        """
        unknown = [k for k in updates if k not in self._SCHEMA]
        if unknown:
            raise ValueError(f"Unknown setting(s): {', '.join(unknown)}")

        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            existing = json.loads(self.settings_path.read_text()) if self.settings_path.exists() else {}
        except (json.JSONDecodeError, OSError):
            existing = {}

        for attr, value in updates.items():
            setattr(self, attr, value)
            existing[attr] = value

        self.settings_path.write_text(json.dumps(existing, indent=2))

    def reset(self, *fields):
        """
        Remove one or more user overrides from settings.json, reverting
        those fields to their .env-derived defaults. With no arguments,
        clears all overrides.
        """
        if not self.settings_path.exists():
            return
        try:
            existing = json.loads(self.settings_path.read_text())
        except (json.JSONDecodeError, OSError):
            existing = {}

        keys_to_clear = fields or list(existing.keys())
        for key in keys_to_clear:
            existing.pop(key, None)

        self.settings_path.write_text(json.dumps(existing, indent=2))
        # Re-derive this instance's values from .env baseline + remaining overrides.
        self.__init__()
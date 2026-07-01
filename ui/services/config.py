# ui/services/config.py
from pathlib import Path
import os
from dotenv import load_dotenv

class Config:
    """Configuration loaded from .env with fallbacks."""
    
    def __init__(self):
        # Look for .env in the app directory
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        
        # Registry settings
        self.registry_url = os.getenv(
            "CLICE_REGISTRY_URL",
            "https://raw.githubusercontent.com/programming-sai/clice-challenges/registry/registry.json"
        )

        self.registry_hash_url = os.getenv(
            "CLICE_REGISTRY_HASH_URL",
            "https://raw.githubusercontent.com/programming-sai/clice-challenges/registry/registry.hash"
        )
        
        # Cache directories
        self.cache_dir = Path(os.getenv("CLICE_CACHE_DIR", str(Path.home() / ".clice" / "cache")))
        self.logs_dir = Path(os.getenv("CLICE_LOGS_DIR", str(Path.cwd() / "assets")))
        
        # Docker settings
        self.docker_timeout = int(os.getenv("CLICE_DOCKER_TIMEOUT", "30"))
        
        # API keys (if any)
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")

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
    """)
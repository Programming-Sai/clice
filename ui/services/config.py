# ui/services/config.py
from pathlib import Path
import os
from dotenv import load_dotenv

class Config:
    """Configuration loaded from .env with fallbacks."""
    
    def __init__(self):
        # Look for .env in the app directory
        possible_paths = [
            Path.cwd() / ".env",  # Current working directory
            Path(__file__).parent.parent.parent / ".env",  # Project root
            Path.home() / ".clice" / ".env",  # User config
        ]
        
        for env_path in possible_paths:
            if env_path.exists():
                load_dotenv(env_path)
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
        
        # Cache directories
        self.cache_dir = Path(os.getenv("CLICE_CACHE_DIR", str(Path.home() / ".clice" / "cache")))
        self.logs_dir = Path(os.getenv("CLICE_LOGS_DIR", str(Path.cwd() / "assets")))
        
        # Docker settings
        self.docker_timeout = int(os.getenv("CLICE_DOCKER_TIMEOUT", "30"))
        
        # API keys (if any)
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat-v3-0324:free")


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
    OPENROUTER_API_KEY=
    OPENROUTER_MODEL=
    """)
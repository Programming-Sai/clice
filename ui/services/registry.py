# ui/services/registry.py
import json
import hashlib
import requests
from pathlib import Path

from ui.services.config import Config

class RegistryService:    
    def __init__(self, config):
        self.config = config or Config()
        self.REGISTRY_URL = self.config.registry_url
        self.HASH_URL = self.config.registry_hash_url
        self.CACHE_DIR = self.config.cache_dir
        self.CACHE_FILE = self.CACHE_DIR / "registry.json"
        self.HASH_FILE  = self.CACHE_DIR / "registry.hash"

        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._challenges = None
        self._is_synced = None
    
    def is_synced(self) -> bool:
        """Check if local registry is in sync with remote."""
        remote_hash = self._get_remote_hash()
        local_hash = self._get_local_hash()
        return remote_hash is not None and local_hash == remote_hash
    
    def _get_remote_hash(self) -> str | None:
        """Fetch the hash from GitHub."""
        try:
            response = requests.get(self.HASH_URL, timeout=5)
            if response.status_code == 200:
                return response.text.strip()
        except:
            pass
        return None
    
    def _get_local_hash(self) -> str | None:
        """Read the local hash file."""
        if not self.HASH_FILE.exists():
            return None
        try:
            return self.HASH_FILE.read_text().strip()
        except:
            return None
    
    def get_challenges(self, force_refresh: bool = False) -> list:
        """Get all challenges from the registry."""
        if force_refresh or not self.CACHE_FILE.exists() or not self.HASH_FILE.exists():
            self._fetch_and_cache()
        return self._load_cache()
    
    def refresh(self) -> list:
        """Force refresh the registry and return updated challenges."""
        self._fetch_and_cache()
        return self._load_cache()
    
    def _fetch_and_cache(self):
        """Fetch registry from GitHub and cache it."""
        try:
            # Fetch both files
            reg_response = requests.get(self.REGISTRY_URL, timeout=10)
            reg_response.raise_for_status()
            data = reg_response.json()
            
            # Save registry
            with open(self.CACHE_FILE, "w") as f:
                json.dump(data, f, indent=2)
            
            # Save hash
            hash_response = requests.get(self.HASH_URL, timeout=5)
            if hash_response.status_code == 200:
                with open(self.HASH_FILE, "w") as f:
                    f.write(hash_response.text.strip())
            
            return data
        except Exception as e:
            if self.CACHE_FILE.exists():
                return self._load_cache()
            raise RuntimeError(f"Failed to fetch registry: {e}")
    
    def _load_cache(self) -> list:
        """Load challenges from cache."""
        with open(self.CACHE_FILE, "r") as f:
            data = json.load(f)
        return data.get("challenges", [])
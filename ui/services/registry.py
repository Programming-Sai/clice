# ui/services/registry.py
import json
import time
import hashlib
import requests
from pathlib import Path

from ui.services.config import Config

class RegistryService:
    # How long a "synced" verdict is trusted before rechecking against the
    # remote hash. Persisted to disk (not just in-memory) because every
    # screen creates its own short-lived RegistryService instance - without
    # this, "is it synced?" meant a live GitHub round-trip on literally every
    # Home mount, every Home resume, and every Browser mount, whether or not
    # anything had actually changed.
    CACHE_TTL_SECONDS = 300

    def __init__(self, config):
        self.config = config or Config()
        self.REGISTRY_URL = self.config.registry_url
        self.HASH_URL = self.config.registry_hash_url
        self.CACHE_DIR = self.config.cache_dir
        self.CACHE_FILE = self.CACHE_DIR / "registry.json"
        self.HASH_FILE  = self.CACHE_DIR / "registry.hash"
        self.LAST_CHECK_FILE = self.CACHE_DIR / "last_sync_check"

        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self._challenges = None
        # Memoized within this instance so a `get_challenges()` call
        # followed by an `is_synced()` call on the same RegistryService
        # (e.g. HomeScreen does exactly this for its status panel) doesn't
        # pay for two separate hash-check round-trips for the same answer.
        self._synced_cache: bool | None = None

    def is_synced(self, force: bool = False) -> bool:
        """Check if local registry is in sync with remote.

        Rate-limited to one real network check per CACHE_TTL_SECONDS (or
        immediately, if `force=True`). Outside that window, and as long as
        a local cache actually exists, we trust the last known answer
        instead of hitting the network again.
        """
        if self._synced_cache is not None and not force:
            return self._synced_cache

        if not force and not self._check_due():
            self._synced_cache = self.CACHE_FILE.exists() and self.HASH_FILE.exists()
            return self._synced_cache

        remote_hash = self._get_remote_hash()
        local_hash = self._get_local_hash()
        self._synced_cache = remote_hash is not None and local_hash == remote_hash
        self._touch_last_checked()
        return self._synced_cache

    def _check_due(self) -> bool:
        if not self.LAST_CHECK_FILE.exists():
            return True
        try:
            last_checked = float(self.LAST_CHECK_FILE.read_text().strip())
        except (OSError, ValueError):
            return True
        return (time.time() - last_checked) > self.CACHE_TTL_SECONDS

    def _touch_last_checked(self) -> None:
        try:
            self.LAST_CHECK_FILE.write_text(str(time.time()))
        except OSError:
            pass

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
        if (
            force_refresh
            or not self.CACHE_FILE.exists()
            or not self.HASH_FILE.exists()
            or not self.is_synced(force=force_refresh)
        ):
            self._fetch_and_cache()
            self._synced_cache = True
            self._touch_last_checked()
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
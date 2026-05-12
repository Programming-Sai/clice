import requests
import json
from pathlib import Path
# import

class ChallengeRegistry:
    REGISTRY_URL = "https://raw.githubusercontent.com/Programming-Sai/clice-challenges/main/registry.json"
    
    def __init__(self):
        self.cache_path = Path.home() / ".clice" / "cache" / "registry.json"
        self.challenges = []
    
    def fetch(self, force_refresh=False):
        """Fetch registry from GitHub (with caching)"""
        if not force_refresh and self.cache_path.exists():
            with open(self.cache_path) as f:
                data = json.load(f)
                self.challenges = data.get("challenges", [])
                return self.challenges
        
        response = requests.get(self.REGISTRY_URL)
        response.raise_for_status()
        data = response.json()
        self.challenges = data.get("challenges", [])
        
        # Cache it
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w") as f:
            json.dump(data, f, indent=2)
        
        return self.challenges
    
    def get_challenge(self, challenge_id):
        """Get specific challenge by ID"""
        if not self.challenges:
            self.fetch()
        for c in self.challenges:
            if c["id"] == challenge_id:
                return c
        return None
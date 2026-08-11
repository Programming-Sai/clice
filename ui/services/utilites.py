import time
import docker


class Utilities:
    # Docker's running/not-running state doesn't change second to second,
    # but get_docker_status() used to create a brand-new client and do a
    # full ping+version handshake on every call - and it's called on every
    # single Home mount/resume. Cache the result briefly so repeat
    # navigation is instant; a manual refresh (force=True) still rechecks.
    _cache: dict | None = None
    _cached_at: float = 0.0
    _CACHE_TTL = 15  # seconds

    def __init__(self):
        pass

    def get_docker_status(self, force: bool = False):
        """Check if Docker is running."""
        now = time.time()
        if (
            not force
            and Utilities._cache is not None
            and (now - Utilities._cached_at) < Utilities._CACHE_TTL
        ):
            return Utilities._cache

        try:
            client = docker.from_env()
            client.ping()
            version = client.version().get("Version", "unknown")
            result = {"status": "ok", "message": f"CONNECTED", "class": "status-ok", "version": version}
        except docker.errors.DockerException:
            result = {"status": "error", "message": "NOT CONNECTED", "class": "status-error", "version": None}
        except Exception:
            result = {"status": "error", "message": "NOT INSTALLED", "class": "status-error", "version": None}

        Utilities._cache = result
        Utilities._cached_at = now
        return result
        
    def get_challenge_registry_sync_status(self):
        pass
        


if __name__ == "__main__":
    svc = Utilities()
    print(svc.get_docker_status())
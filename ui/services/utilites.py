

import docker


class Utilities:
    def __init__(self):
        pass

    def get_docker_status(self):
        """Check if Docker is running."""
        try:
            client = docker.from_env()
            client.ping()
            version = client.version().get("Version", "unknown")
            return {"status": "ok", "message": f"CONNECTED", "class": "status-ok", "version":version}
        except docker.errors.DockerException:
            return {"status": "error", "message": "NOT CONNECTED", "class": "status-error", "version":None}
        except Exception:
            return {"status": "error", "message": "NOT INSTALLED", "class": "status-error", "version":None}
        
    def get_challenge_registry_sync_status(self):
        pass
        


if __name__ == "__main__":
    svc = Utilities()
    print(svc.get_docker_status())
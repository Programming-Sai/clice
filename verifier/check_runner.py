import docker
import tempfile
import requests
from pathlib import Path

class CheckRunner:
    def __init__(self):
        self.docker = docker.from_env()
        self.checker_images = {}  # Cache of built images per challenge
    
    def verify(self, challenge_id, user_container_id, check_url):
        """Run verification check in isolated container"""
        
        # 1. Download check.py
        response = requests.get(check_url)
        response.raise_for_status()
        check_script = response.text
        
        # 2. Build or reuse checker image for this challenge
        image_name = f"clice-checker-{challenge_id}:latest"
        
        if image_name not in self.checker_images:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write check.py to temp file
                script_path = Path(tmpdir) / "check.py"
                script_path.write_text(check_script)
                
                # Create Dockerfile
                dockerfile = """
FROM python:3.10-slim
COPY check.py /check.py
WORKDIR /
ENTRYPOINT ["python", "/check.py"]
"""
                (Path(tmpdir) / "Dockerfile").write_text(dockerfile)
                
                # Build the image
                self.docker.images.build(
                    path=tmpdir,
                    tag=image_name,
                    rm=True
                )
                self.checker_images[image_name] = True
        
        # 3. Run checker container
        checker = self.docker.containers.run(
            image_name,
            # Mount user container's workspace
            volumes_from=[user_container_id],
            # No network (can't exfiltrate)
            network_disabled=True,
            # Memory limit
            mem_limit="50m",
            # CPU limit (50% of one CPU)
            nano_cpus=500000000,
            # Read-only root
            read_only=True,
            # Remove after execution
            remove=True,
            detach=False
        )
        
        # 4. Return result (exit code 0 = pass)
        return checker.return_code == 0
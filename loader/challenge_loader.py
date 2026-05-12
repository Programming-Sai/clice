import docker
import tempfile
import requests
from pathlib import Path

class ChallengeLoader:
    def __init__(self):
        self.docker = docker.from_env()
        self.checker_images = {}
        self.volume_name = None
    
    def load_challenge(self, challenge_info):
        """Pull challenge image, build checker image, return container"""
        
        # 1. Pull challenge image
        image_name = challenge_info["image"]
        print(f"Pulling {image_name}...")
        self.docker.images.pull(image_name)
        
        # 2. Build checker image
        self._build_checker_image(challenge_info)
        
        # 3. Create shared volume
        volume_name = f"clice-workspace-{challenge_info['id']}"
        try:
            # Remove old volume if exists
            old_volume = self.docker.volumes.get(volume_name)
            old_volume.remove()
        except:
            pass
        self.docker.volumes.create(name=volume_name)
        self.volume_name = volume_name
        
        # 4. Start user container
        container = self.docker.containers.run(
            challenge_info["image"],
            command=["tail", "-f", "/dev/null"],
            detach=True,
            stdin_open=True,
            tty=True,
            volumes={volume_name: {"bind": "/workspace", "mode": "rw"}},
            name=f"clice-{challenge_info['id']}"
        )
        
        # Verify container is running
        import time
        time.sleep(1)
        container.reload()
        if container.status != 'running':
            raise RuntimeError(f"Container {container.id} failed to start: {container.status}")
        
        return container
    
    def _build_checker_image(self, challenge_info):
        """Build isolated checker image for this challenge (cached)"""
        challenge_id = challenge_info["id"]
        check_url = challenge_info["check_url"]
        image_tag = f"clice-checker-{challenge_id}:latest"
        
        # Check if already built
        try:
            self.docker.images.get(image_tag)
            self.checker_images[challenge_id] = image_tag
            print(f"Checker image already cached for {challenge_id}")
            return
        except docker.errors.ImageNotFound:
            pass
        
        # Download check.py
        print(f"Downloading check script for {challenge_id}...")
        response = requests.get(check_url)
        response.raise_for_status()
        check_script = response.text
        
        # Build checker image
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "check.py"
            script_path.write_text(check_script)
            
            dockerfile = """
FROM python:3.10-slim
COPY check.py /check.py
WORKDIR /
ENTRYPOINT ["python", "/check.py"]
"""
            (Path(tmpdir) / "Dockerfile").write_text(dockerfile)
            
            print(f"Building checker image for {challenge_id}...")
            self.docker.images.build(
                path=tmpdir,
                tag=image_tag,
                rm=True
            )
            self.checker_images[challenge_id] = image_tag
            print(f"Checker image built: {image_tag}")
    
    def verify(self, challenge_id, user_container):
        """Run verification using pre-built checker image"""
        image_tag = self.checker_images.get(challenge_id)
        if not image_tag:
            raise ValueError(f"No checker image for {challenge_id}")
        
        # Create and run checker container
        try:
            container = self.docker.containers.create(
                image_tag,
                volumes={self.volume_name: {"bind": "/workspace", "mode": "ro"}},
                network_disabled=True,
                mem_limit="50m",
                nano_cpus=500000000,
                read_only=True,
            )
            
            container.start()
            result = container.wait()
            exit_code = result["StatusCode"]
            
            # Get logs
            logs = container.logs().decode().strip()
            if logs:
                print("Checker output:", logs)
            else:
                print("NO Logs")
            
            # Clean up
            container.remove()
            
            return exit_code == 0
            
        except Exception as e:
            print(f"Verification error: {e}")
            return False
    
    def cleanup(self, container):
        """Stop and remove user container and volume"""
        try:
            container.stop()
            container.remove()
        except:
            pass
        
        try:
            if hasattr(self, 'volume_name') and self.volume_name:
                volume = self.docker.volumes.get(self.volume_name)
                volume.remove()
        except:
            pass
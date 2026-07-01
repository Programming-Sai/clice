# ui/widgets/home/ready.py
from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Horizontal


class ReadyPanel(Static):
    def compose(self) -> ComposeResult:
        yield Static("║ SYSTEM STATUS ║", classes="panel-title")

        with Horizontal(classes="check-row"):
            yield Static("Docker engine", classes="check-label")
            self.docker_status = Static("\[...]", classes="check-ok")
            yield self.docker_status

        with Horizontal(classes="check-row"):
            yield Static("Challenge registry", classes="check-label")
            self.registry_status = Static("\[...]", classes="check-ok")
            yield self.registry_status

        with Horizontal(classes="check-row"):
            yield Static("Challenges available", classes="check-label")
            self.challenge_count = Static("\[...]", classes="check-ok")
            yield self.challenge_count

    def on_mount(self) -> None:
        self.border_title = "02 / READY TO START?"

    def update_status(self, docker_status: dict, registry_status: str, challenge_count: int) -> None:
        """Update all status indicators from HomeScreen."""
        self._update_docker_status(docker_status)
        self._update_registry_status(registry_status)
        self._update_challenge_count(challenge_count)

    def _update_docker_status(self, status: dict) -> None:
        status_text = status['message']
        is_ok = status['status'] == 'ok'
        
        self.docker_status.update(f"\[{status_text}]")
        self.docker_status.remove_class("check-ok", "check-fail")
        self.docker_status.add_class("check-ok" if is_ok else "check-fail")

    def _update_registry_status(self, status_text: str) -> None:
        is_synced = status_text == "SYNCED"
        self.registry_status.update(f"\[{status_text}]")
        self.registry_status.remove_class("check-ok", "check-fail")
        self.registry_status.add_class("check-ok" if is_synced else "check-fail")

    def _update_challenge_count(self, count: int) -> None:
        self.challenge_count.update(f"\[{count}]")
        self.challenge_count.remove_class("check-ok", "check-fail")
        self.challenge_count.add_class("check-ok" if count > 0 else "check-fail")
# ui/screens/home.py
from pathlib import Path
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static
from textual.binding import Binding
from ui.widgets.footer import Footer

from ..widgets.home.logo import LogoWidget
from ..widgets.home.about import AboutPanel
from ..widgets.home.ready import ReadyPanel
from ..widgets.home.activity import ActivityPanel

from ui.services.utilites import Utilities
from ui.services.registry import RegistryService
from ui.services.config import Config


class HomeScreen(Screen):
    """Home screen with its own CSS"""
    
    CSS_PATH = Path(__file__).parent / "home.tcss"
    
    BINDINGS = [
        Binding("r", "refresh", "Refresh", show=True),
    ]

    def compose(self):
        with Horizontal(id="header"):
            with Vertical(id="header-center"):
                yield LogoWidget(id="logo-area")
                yield Static("Command Line Interface Competence Evaluator", id="app-tagline")
        
        with Horizontal(id="main-row"):
            with Vertical(id="left-col"):
                self.ready_panel = ReadyPanel(classes="panel")
                yield self.ready_panel
                yield AboutPanel(classes="panel")
            with Vertical(id="right-col"):
                yield ActivityPanel(classes="panel")
        
        yield Footer()
        
    def on_mount(self) -> None:
        self.query_one(Footer).set_screen("home")
        self._update_status()

    def action_refresh(self) -> None:
        """Refresh all status indicators (key: R)."""
        self._update_status(force=True)
        self.notify("Status refreshed", title="CLICE", timeout=1)

    def _update_status(self, force=False) -> None:
        """Fetch all status data and update the ready panel."""
        config = Config()
        registry = RegistryService(config)
        
        # Get Docker status
        docker_status = Utilities().get_docker_status()
        
        # Get Registry status – fetch if cache doesn't exist
        try:
            # This ensures we have the registry cached
            challenges = registry.get_challenges(force_refresh=force)  # ← Fetches if cache doesn't exist
            challenge_count = len(challenges)
            
            # Now check sync status
            registry_status = "SYNCED" if registry.is_synced() else "OUT OF SYNC"
        except Exception as e:
            registry_status = "ERROR"
            challenge_count = 0
        
        # Update the ready panel
        self.ready_panel.update_status(docker_status, registry_status, challenge_count)
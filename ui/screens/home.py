# ui/screens/home.py
from pathlib import Path
from textual import work
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._refresh_in_progress = False

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
        self._start_refresh(force=False)

    def on_screen_resume(self) -> None:
        """Fires every time this screen becomes the active one again -
        including when popped back to (e.g. finishing a challenge and
        returning here), unlike on_mount which only ever fires once for
        this cached screen instance. This is what makes a just-completed
        session actually show up without requiring a manual [r] press."""
        self._start_refresh(force=False)

    def action_refresh(self) -> None:
        """Refresh all status indicators (key: R)."""
        if self._refresh_in_progress:
            self.notify("Already refreshing...", title="CLICE", timeout=1)
            return
        self._start_refresh(force=True)

    def _start_refresh(self, force: bool) -> None:
        self._refresh_in_progress = True
        self._do_refresh(force)

    @work(thread=True)
    def _do_refresh(self, force: bool) -> None:
        """Fetch registry/docker status in the background - this used to
        run synchronously on the main thread, which meant any network call
        (registry fetch) froze the entire TUI until it finished."""
        config = Config()
        registry = RegistryService(config)

        docker_status = Utilities().get_docker_status(force=force)

        try:
            challenges = registry.get_challenges(force_refresh=force)
            challenge_count = len(challenges)
            registry_status = "SYNCED" if registry.is_synced() else "OUT OF SYNC"
        except Exception:
            registry_status = "ERROR"
            challenge_count = 0

        self.app.call_from_thread(
            self._apply_refresh_results, docker_status, registry_status, challenge_count, force
        )

    def _apply_refresh_results(self, docker_status, registry_status, challenge_count, force) -> None:
        self.ready_panel.update_status(docker_status, registry_status, challenge_count)
        # Wired to refresh everything on this screen, not just the ready
        # panel - a completed session's result shows up here too now,
        # whether this ran automatically (on_screen_resume) or manually ([r]).
        self.query_one(ActivityPanel).refresh_sessions()

        self._refresh_in_progress = False
        if force:
            self.notify("Status refreshed", title="CLICE", timeout=1)
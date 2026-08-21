# ui/main.py
from pathlib import Path
from textual import work
from textual.app import App
from textual.screen import Screen
from textual.widgets import Static
from ui.screens import HomeScreen, BrowserScreen
from ui.screens.history import HistoryScreen
from ui.screens.session import SessionScreen
from ui.screens.settings import SettingsScreen
from ui.screens.verdict import VerdictScreen
from ui.widgets.footer import Footer   # or from .screens import ...
from loader.challenge_loader import ChallengeLoader
from logger.debug import trace


class LoadingScreen(Screen):
    """Minimal placeholder shown while `clice open <id>` is pulling/starting
    a container - pushed immediately in on_mount, before Home ever gets a
    chance to render, so `open` goes straight to a loading state instead of
    flashing the full interactive Home screen first."""

    DEFAULT_CSS = """
    LoadingScreen {
        align: center middle;
        background: $surface;
    }
    #loading-message {
        color: $text-muted;
        width: auto;
        height: auto;
    }
    """

    def __init__(self, message: str = "Loading challenge...", **kwargs):
        super().__init__(**kwargs)
        self.message = message

    def compose(self):
        yield Static(self.message, id="loading-message")


class CliceApp(App):
    """Main CLICE Application"""
    
    ansi_color = True

    def __init__(self, initial_challenge: dict | None = None, initial_screen: str | None = None, **kwargs):
        """initial_challenge: skip Home and load straight into this
        challenge's session (used by `clice open <id>`).
        initial_screen: push this named screen instead of "home" (used by
        `clice history`/`clice settings`/`clice browser`)."""
        super().__init__(**kwargs)
        self.initial_challenge = initial_challenge
        self.initial_screen = initial_screen
    
    # Shared base CSS (applies to all screens)
    CSS = """
    /* Global styles that apply everywhere */
    * {
        scrollbar-size: 0 0;
    }

    /* Footer should dock at bottom */
    #footer-container {
        height: 1;
        layout: horizontal;
        margin-top:1;
    }
    
    #footer-left {
        width: 1fr;
        height: 1;
        content-align: left middle;
    }
    
    #footer-right {
        width: auto;
        height: 1;
        content-align: right middle;
        color: #00e5cc;
    }

    """
    
    BINDINGS = [
        ("n", "new_session", "NEW_SESSION"),
        ("x", "home",     "HOME"),
        ("b", "browser",     "BROWSER"),
        ("h", "history",     "HISTORY"),
        ("s", "settings",    "SETTINGS"),
        ("q", "quit",        "QUIT"),
    ]
    
    # Register screens
    SCREENS = {
        "home":     HomeScreen,
        "browser":  BrowserScreen,
        "session":  SessionScreen,
        "verdict":  VerdictScreen,
        "history":  HistoryScreen,
        "settings": SettingsScreen,
    }

    
    def on_mount(self):
        trace("app_on_mount", initial_challenge=bool(self.initial_challenge), initial_screen=self.initial_screen)
        if self.initial_challenge:
            # Deliberately do NOT push "home" here at all. Pushing it and
            # immediately covering it with LoadingScreen was the previous
            # attempt at this fix, on the assumption that two push_screen
            # calls in one synchronous on_mount can't produce an
            # intermediate paint - that assumption turned out to be wrong
            # in practice (mounting Home, including reading its .tcss file
            # from disk, appears to trigger a real, visible render before
            # control ever returns here). The only way to guarantee Home
            # is never visible is to never mount it in the first place.
            # See pop_screen() below for how "back" still works correctly
            # without Home having been pre-populated on the stack.
            self.push_screen(LoadingScreen(f"Loading {self.initial_challenge.get('title', self.initial_challenge.get('code', 'challenge'))}..."))
            self._open_initial_challenge()
        elif self.initial_screen and self.initial_screen != "home":
            self.push_screen(self.initial_screen)
        else:
            self.push_screen("home")

    def pop_screen(self):
        """Safety net: normally each screen's own back-navigation handles
        popping itself, but since `clice open` never pre-populates Home
        on the stack (see on_mount above), popping all the way past
        Session/Verdict would otherwise leave the app with an empty
        screen stack, or briefly exposed LoadingScreen, neither of which
        should ever be user-facing. Whenever that would happen, land on
        Home instead - created fresh, on demand, only when actually
        needed rather than pre-mounted and hidden."""
        try:
            result = super().pop_screen()
        except Exception:
            result = None
        if not self.screen_stack or isinstance(self.screen, LoadingScreen):
            self.push_screen("home")
        return result

    @work(thread=True)
    def _open_initial_challenge(self) -> None:
        """Load and jump straight into a specific challenge's session,
        mirroring BrowserScreen's own start-challenge flow exactly, since
        this needs to behave identically to picking it from the browser -
        just skipping the navigation."""
        challenge = self.initial_challenge
        try:
            loader = ChallengeLoader()
            container = loader.load_challenge(challenge)
            container.reload()
            if container.status != "running":
                raise RuntimeError(f"Container not running: {container.status}")
        except Exception as e:
            trace("cli_open_load_failed", error=str(e))
            self.call_from_thread(self._on_initial_challenge_failed, str(e))
            return

        self.call_from_thread(self._on_initial_challenge_ready, challenge, container, loader)

    def _on_initial_challenge_ready(self, challenge, container, loader) -> None:
        # switch_screen replaces the current top screen (Loading) with
        # Session directly, in one atomic step - no intermediate empty
        # stack, so the pop_screen safety net above never fires here.
        self.switch_screen(SessionScreen(challenge, True, True, container, loader=loader))

    def _on_initial_challenge_failed(self, error: str) -> None:
        # Same reasoning: switch straight to Home instead of popping
        # Loading (which would leave the stack momentarily empty) and
        # then pushing Home as a separate step.
        self.switch_screen("home")
        self.notify(f"Failed to start challenge: {error}", title="Error", severity="error")
    
    def action_new_session(self) -> None:
        self.notify("🖥  NEW_SESSION — not yet implemented!", title="CLICE")
    
    def action_browser(self) -> None:
        """Navigate to challenge browser"""
        self.push_screen("browser")  # ← FIXED: actually push the screen

    def action_home(self) -> None:
        """Navigate to challenge home"""
        self.push_screen("home")  # ← FIXED: actually push the screen
    
    def action_history(self) -> None:
        self.push_screen("history")
    
    def action_settings(self) -> None:
        self.push_screen("settings")

def run(initial_challenge: dict | None = None, initial_screen: str | None = None):
    trace("app_run")
    app = CliceApp(initial_challenge=initial_challenge, initial_screen=initial_screen)
    app.run()

if __name__ == "__main__":
    run()


# TODO we need to have a unified prompt text. right now it is hard coded. we need one directly from the session itself.
""" 
TODO edge cases to check out for.

- What happens when you close the app in the middle of a session
- what happens when you close out in the middle of any screen
- what happwns if you close out in the middle of transitions between screens 
"""


# clice open <> does not open the challenge. it opens everything.
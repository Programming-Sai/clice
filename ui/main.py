# ui/main.py
from pathlib import Path
from textual import work
from textual.app import App
from ui.screens import HomeScreen, BrowserScreen
from ui.screens.history import HistoryScreen
from ui.screens.session import SessionScreen
from ui.screens.settings import SettingsScreen
from ui.screens.verdict import VerdictScreen
from ui.widgets.footer import Footer   # or from .screens import ...
from loader.challenge_loader import ChallengeLoader
from logger.debug import trace


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
        self.push_screen("home")
        if self.initial_challenge:
            # Home stays underneath on the stack, so "back" from the
            # session screen lands somewhere sensible instead of an
            # empty app.
            self._open_initial_challenge()
        elif self.initial_screen and self.initial_screen != "home":
            self.push_screen(self.initial_screen)

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
            self.call_from_thread(
                self.notify, f"Failed to start challenge: {e}", title="Error", severity="error"
            )
            return

        self.call_from_thread(
            self.push_screen, SessionScreen(challenge, True, True, container, loader=loader)
        )
    
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
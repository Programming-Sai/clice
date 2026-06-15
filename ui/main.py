# ui/main.py
from pathlib import Path
from textual.app import App
from ui.screens import HomeScreen, BrowserScreen
from ui.screens.session import SessionScreen
from ui.screens.verdict import VerdictScreen   # or from .screens import ...


class CliceApp(App):
    """Main CLICE Application"""
    
    ansi_color = True
    
    # Shared base CSS (applies to all screens)
    CSS = """
    /* Global styles that apply everywhere */
    * {
        scrollbar-size: 0 0;
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
        "home": HomeScreen,
        "browser": BrowserScreen,
        "session": SessionScreen,
        "verdict": VerdictScreen,
    }
    
    def on_mount(self):
        self.push_screen("home")
    
    def action_new_session(self) -> None:
        self.notify("🖥  NEW_SESSION — not yet implemented!", title="CLICE")
    
    def action_browser(self) -> None:
        """Navigate to challenge browser"""
        self.push_screen("browser")  # ← FIXED: actually push the screen

    def action_home(self) -> None:
        """Navigate to challenge home"""
        self.push_screen("home")  # ← FIXED: actually push the screen
    
    def action_history(self) -> None:
        self.notify("📜  HISTORY — not yet implemented!", title="CLICE")
    
    def action_settings(self) -> None:
        self.notify("⚙️  SETTINGS — not yet implemented!", title="CLICE")

def run():
    app = CliceApp()
    app.run()

if __name__ == "__main__":
    run()



# TODO we need to make the home screen as responsive as the verdict screen
# TODO we need to include loading states, for when we actually need laoding
# TODO we need to have a centralised footer
# TODO we need to tract activity history and do proper routing for that... so on th ehome page, you view your past activities, and then when you select one, you go to its verdict screen and from there... you can redo it which you can choose to use to overwrite your previous score or to do a new instance of that same problem.
# TODO the sessino history is not specific to a problem, but more of a global thing. we need to fix that.
# TODO we need to have a unified design system for the entire app.
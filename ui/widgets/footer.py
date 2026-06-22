# ui/widgets/footer.py
from textual.widgets import Static
from textual.containers import Horizontal
from textual.app import ComposeResult

class Footer(Static):
    """Screen-aware footer that updates based on current screen."""

    BINDING_SETS = {
        "home": [
            ("N", "NEW_SESSION"),
            ("B", "BROWSER"),
            ("H", "HISTORY"),
            ("S", "SETTINGS"),
            ("R", "REFRESH"),
            ("Q", "QUIT"),
        ],
        "browser": [
            ("↑/↓", "NAVIGATE"),
            ("/", "SEARCH"),
            ("Alt+X", "START"),
            ("Esc", "BACK"),
            ("Q", "QUIT"),
        ],
        "session": [
            ("Ctrl+S", "SUBMIT"),
            ("Ctrl+D", "CHALLENGE"),
            ("Ctrl+H", "HELP"),
            ("Ctrl+L", "CLEAR"),
            ("Ctrl+T", "TIMER"),
            ("Esc", "BACK"),
        ],
        "verdict": [
            ("Enter", "BROWSER"),
            ("H", "HISTORY"),
            ("Q", "QUIT"),
        ],
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._current_screen = "home"
        self._right_content = ""

    def set_screen(self, screen_name: str) -> None:
        self._current_screen = screen_name
        self._update_display()

    def set_right_content(self, content: str) -> None:
        self._right_content = content
        self._update_display()

    def _update_display(self) -> None:
        # Left: bindings
        bindings = self.BINDING_SETS.get(self._current_screen, [])
        parts = []
        for key, label in bindings:
            parts.append(f"[bold #00e5cc on #1a2e2e] {key} [/] [#888888]{label}[/]")
        left_content = "  ".join(parts)
        
        self.query_one("#footer-left", Static).update(left_content)
        self.query_one("#footer-right", Static).update(self._right_content)

    def compose(self) -> ComposeResult:
        with Horizontal(id="footer-container"):
            yield Static("", id="footer-left")
            yield Static("", id="footer-right")

    def on_mount(self) -> None:
        self._update_display()
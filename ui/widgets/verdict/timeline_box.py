from textual.containers import ScrollableContainer
from textual.widgets import Static
from textual.app import ComposeResult
from rich.text import Text
from ui.widgets.utils.design import BRAND, TEXT, ACCENT_OK, ACCENT_ERR
from ui.widgets.verdict.eof_marker import EOFMarker

class TimelineRow(Static):
    """Single log line."""

    def __init__(self, timestamp: str, command: str, exit_code: str, is_passing: bool, **kwargs):
        super().__init__(**kwargs)
        self.timestamp = timestamp
        self.command = command
        self.exit_code = exit_code
        self.is_passing = is_passing

    def render(self) -> Text:
        t = Text()
        t.append(self.timestamp + " ", style=f"dim {BRAND}")
        t.append("▌ ", style=BRAND)
        t.append(f"{self.command:<52}", style=TEXT)
        exit_style = ACCENT_OK if self.is_passing else ACCENT_ERR
        t.append(self.exit_code, style=exit_style)
        return t


class TimelineBox(ScrollableContainer):
    """Scrollable timeline of commands."""

    def __init__(self, session_log: dict, **kwargs):
        super().__init__(**kwargs)
        self.session_log = session_log
        self.goal_reached = session_log.get("goal_reached", False)
        self.commands = session_log.get("commands", [])

    def compose(self) -> ComposeResult:
        yield Static("", id="timeline-label")  # Will be replaced by border_title
        if not self.commands:
            yield Static("No commands recorded.", id="empty-timeline")
        else:
            for cmd in self.commands[:20]:  # Limit to 20 rows
                ts = cmd.get("timestamp", "[--:--:--]")
                command = cmd.get("command", "")
                exit_code = cmd.get("exit_code", 0)
                yield TimelineRow(f"[{ts}]" if ts != "[--:--:--]" else ts, command, f"({exit_code})", self.goal_reached)
        yield EOFMarker()

    def on_mount(self):
        self.border_title = "║ TIMELINE ║"
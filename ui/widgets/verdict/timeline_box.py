from textual.containers import Horizontal, ScrollableContainer
from textual.widgets import Static
from textual.app import ComposeResult
from rich.text import Text
from ui.widgets.utils.design import BRAND, TEXT, ACCENT_OK, ACCENT_ERR
from ui.widgets.verdict.eof_marker import EOFMarker

class TimelineRow(Horizontal):
    """Single log line with timestamp, command, and right-aligned exit code."""

    DEFAULT_CSS = """
    TimelineRow {
        width: 100%;
        height: 1;
        padding: 0 1;
    }
    #timeline-prefix {
        width: auto;
        height: 1;
    }
    #timeline-command {
        width: 1fr;
        height: 1;
        padding-left: 1;
    }
    #timeline-exit {
        width: auto;
        height: 1;
        padding-left: 2;
    }
    """

    def __init__(self, timestamp: str, command: str, exit_code: str, **kwargs):
        super().__init__(**kwargs)
        self.timestamp = timestamp
        self.command = command if command else "(empty command)"
        self.exit_code = exit_code
        self.exit_code_int = int(exit_code.strip("()"))

    def compose(self) -> ComposeResult:
        yield Static(self.timestamp + " ▌", id="timeline-prefix")
        yield Static(self.command, id="timeline-command")
        yield Static(self.exit_code, id="timeline-exit")

    def on_mount(self):
        self.query_one("#timeline-prefix").styles.color = BRAND
        self.query_one("#timeline-command").styles.color = TEXT
        
        exit_widget = self.query_one("#timeline-exit")
        exit_widget.styles.color = ACCENT_OK if self.exit_code_int == 0 else ACCENT_ERR

        

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
            # Calculate padding width based on total commands
            total = len(self.commands)
            width = len(str(total))
            for cmd in self.commands[:20]:  # Limit to 20 rows
                ts = cmd.get("timestamp", "")
                if not ts:
                    # Fallback: use index as timestamp
                    ts = f"#{str(cmd.get('index', 0)).zfill(width)}"
                else:
                    ts = f"{ts}"
                command = cmd.get("command", "")
                exit_code = cmd.get("exit_code", 0)
                yield TimelineRow(f"[{ts}]" if ts != "[--:--:--]" else ts, command, f"({exit_code})")
        yield EOFMarker()

    def on_mount(self):
        self.border_title = "║ TIMELINE ║"
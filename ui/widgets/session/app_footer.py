

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static






# ══════════════════════════════════════════════════════════════════════════════
#  WIDGET: AppFooter
# ══════════════════════════════════════════════════════════════════════════════



class AppFooter(Horizontal):
    DEFAULT_CSS = """
    AppFooter {
        height: 1;
        background: #0d1a0d;
        dock: bottom;
    }
    #footer-keys {
        width: 1fr;
        height: 1;
        color: #888888;
        background: #0d1a0d;
        padding: 0 1;
        content-align: left middle;
    }
    #footer-timer {
        width: auto;
        height: 1;
        color: #00e5cc;
        background: #0d1a0d;
        padding: 0 2;
        content-align: right middle;
        display: none;
    }
    #footer-timer.visible {
        display: block;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(
            "[bold #00e5cc on #1a2e2e] ^Q [/][#888888] QUIT [/]"
            "[bold #00e5cc on #1a2e2e] ^S [/][#888888] SUBMIT [/]"
            "[bold #00e5cc on #1a2e2e] ^D [/][#888888] CHALLENGE [/]"
            "[bold #00e5cc on #1a2e2e] ^H [/][#888888] HELP [/]"
            "[bold #00e5cc on #1a2e2e] ^L [/][#888888] CLEAR [/]"
            "[bold #00e5cc on #1a2e2e] ^T [/][#888888] TIMER [/]",
            id="footer-keys"
        )
        yield Static("", id="footer-timer")

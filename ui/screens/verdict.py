# ui/screens/verdict.py
"""
VerdictScreen — Results screen for CLICE challenge completion
==============================================================
Layout priority:
  1. SYSTEM_VERDICT  — the big story (right, 62%, tall hero row)
  2. METRICS         — the numbers + challenge metadata (left, 38%, same hero row)
  3. TIMELINE        — the raw log (slim strip at the bottom, always visible)
"""

from textual.screen import Screen
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static


from ui.screens.data.verdicts import VERDICT_MD_FAIL, VERDICT_MD_PASS
from ui.widgets.footer import Footer
from ui.widgets.utils.design import (
    BRAND, ACCENT_OK, DIM_BRAND, BG, TEXT
)
from ui.widgets.verdict.eof_marker import EOFMarker
from ui.widgets.verdict.metrics_panel import MetricsPanel
from ui.widgets.verdict.timeline_box import TimelineBox
from ui.widgets.verdict.title import BigTitle
from ui.widgets.verdict.verdict_markdown import VerdictMarkdown




# ══════════════════════════════════════════════════════════════════════════════
#  VERDICT SCREEN
# ══════════════════════════════════════════════════════════════════════════════

class VerdictScreen(Screen):
    """Results screen for a completed challenge session."""

    CSS = f"""
    Screen {{
        background: {BG};
        color: {TEXT};
    }}

    #root-container {{
        width: 100%;
        height: 100%;
        padding: 1 2;
    }}

    BigTitle {{
        width: 100%;
        content-align: center middle;
        height: 8;
        margin-bottom: 1;
    }}

    #hero-row {{
        width: 100%;
        height: 1fr;
        margin-bottom: 1;
    }}

    #metrics-box {{
        width: 38%;
        border: solid {DIM_BRAND};
        padding: 0 1;
        height: 100%;
        overflow-y: auto;
    }}

    #verdict-box {{
        width: 62%;
        border: solid {DIM_BRAND};
        padding: 0 1;
        height: 100%;
        margin-left: 1;
    }}

    VerdictMarkdown {{
        background: transparent;
        color: {TEXT};
        padding: 1 1;
        height: 100%;
        overflow-y: auto;
    }}

    VerdictMarkdown MarkdownH2 {{
        color: {BRAND};
        text-style: bold;
    }}

    VerdictMarkdown MarkdownH3 {{
        color: {ACCENT_OK};
        text-style: bold;
    }}

    VerdictMarkdown MarkdownFence {{
        background: #0c1f1c;
        color: {ACCENT_OK};
        padding: 0 1;
    }}

    VerdictMarkdown MarkdownInlineCode {{
        color: {BRAND};
        text-style: bold;
    }}

    #metrics-box, VerdictMarkdown, #timeline-box {{
        scrollbar-size-vertical: 1;
        scrollbar-color: {BRAND};
        scrollbar-background: #0d1a0d;
        scrollbar-color-hover: #00ffff;
        scrollbar-color-active: {ACCENT_OK};
    }}

    #timeline-box {{
        width: 100%;
        height: 10;
        border: solid {DIM_BRAND};
        padding: 0 2;
        padding-top: 1;
        overflow-y: auto;
    }}

    TimelineRow {{
        height: 1;
        width: 100%;
    }}

    EOFMarker {{
        height: 1;
        margin-top: 1;
    }}

    #footer-bar {{
        width: 100%;
        height: 1;
        background: {DIM_BRAND};
        color: {BRAND};
        dock: bottom;
        padding: 0 2;
        content-align: left middle;
    }}
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("enter", "return_back", "Back"),
        ("h", "view_history", "View History"),
    ]

    def __init__(self, challenge: dict, session_log: dict = None, **kwargs):
        super().__init__(**kwargs)
        self.challenge = challenge
        self.session_log = session_log or {}
        self.is_passing = self.session_log.get("goal_reached", False)
        self.verdict_md = VERDICT_MD_PASS if self.is_passing else VERDICT_MD_FAIL
        self.timeline_rows = self._build_timeline()

    def _build_timeline(self):
        """Build timeline from session log commands."""
        commands = self.session_log.get("commands", [])
        if not commands:
            return [
                ("[--:--:--]", "No commands recorded", "(0)")
            ]
        rows = []
        for cmd in commands:
            ts = cmd.get("timestamp", "")
            command = cmd.get("command", "")
            exit_code = cmd.get("exit_code", 0)
            rows.append((f"[{ts}]" if ts else "[--:--:--]", command, f"({exit_code})"))
        return rows

    def compose(self) -> ComposeResult:
        with Vertical(id="root-container"):
            yield BigTitle(self.is_passing)

            with Horizontal(id="hero-row"):
                with Vertical(id="metrics-box"):
                    yield MetricsPanel(self.challenge, self.is_passing)
                with Vertical(id="verdict-box"):
                    yield VerdictMarkdown(self.verdict_md, id="verdict-md")

            with ScrollableContainer(id="timeline-box"):
                yield TimelineBox(self.session_log)
                # yield EOFMarker()

            yield Footer()

    def on_mount(self) -> None:
        self.query_one(Footer).set_screen("verdict")
        result_word = "PASS" if self.is_passing else "FAIL"
        self.title = f"{result_word} — {self.challenge['id']} {self.challenge['title']}"
        self.query_one("#metrics-box").border_title = "║ METRICS ║"
        self.query_one("#verdict-box").border_title = "║ SYSTEM_VERDICT ║"
        self.query_one("#timeline-box").border_title = "║ TIMELINE ║"

    def action_return_back(self) -> None:
        self.app.pop_screen()

    def action_view_history(self) -> None:
        self.notify("History view coming soon", title="CLICE")

    def action_quit(self) -> None:
        self.app.exit()


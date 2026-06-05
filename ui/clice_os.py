"""
CLICE_OS Terminal UI — built with Python Textual
=================================================
"""

import random
import time
from datetime import datetime

import psutil

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widget import Widget
from textual.widgets import Footer, Input, RichLog, Static, Markdown
from ui.screens.data.challenges import CHALLENGES


# ─── CSS ──────────────────────────────────────────────────────────────────────
DEFAULT_CSS = """
/* ── SCREEN ── */
Screen {
    background: #0a0a0a;
    color: #c8ffc8;
    layout: vertical;
}

/* Main horizontal layout (terminal + sidebar) */
#main-horizontal {
    height: 1fr;
    layout: horizontal;
}

/* Terminal area (takes remaining space when sidebar is visible) */
#terminal-area {
    width: 1fr;
    layout: vertical;
    background: #0a0a0a;
    # background: red;
}

/* ── SCROLLABLE TERMINAL AREA ── */
#terminal-scroll {
    height: 1fr;
    overflow-y: auto;
    background: #0d0d0d;
    # background: red;
    padding: 0 1;
}

/* ── OUTPUT LOG ── */
#output-log {
    height: auto;
    background: #0d0d0d;
    # background: blue;
    border: none;
    padding: 0;
    color: #cccccc;
}

/* ── PROMPT ROW ── */
#prompt-row {
    height: 1;
    layout: horizontal;
    background: #0d0d0d;
    padding: 0;
    align: left middle;
}

#prompt-label {
    width: auto;
    color: #00e5cc;
    content-align: left middle;
    padding: 0 1 0 0;
}

#cmd-input {
    width: 1fr;
    background: #0d0d0d;
    border: none;
    color: #f0fafa;
    padding: 0;
}
#cmd-input:focus {
    border: none;
    background: #0d0d0d;
}
#cmd-input > .input--cursor {
    background: #1a2e2e;
    color: #ffffff;
}
#cmd-input > .input--suggestion {
    color: #446666;
}



/* ── SIDEBAR (RIGHT PANEL) ── */
#sidebar {
    display: none;          /* Completely removed from layout when hidden */
    background: #0d1a0d;
    border-left: solid #1e3a3a;
    padding: 1 2;
}

#sidebar.visible {
    display: block;         /* Show only when toggled */
    width: 30%;
}

#sidebar-header {
    color: #00ffff;
    text-style: bold;
    margin-bottom: 1;
    border-bottom: solid #1e3a3a;
    padding: 0 0 1 0;
}

#sidebar-content {
    height: 1fr;
    overflow-y: auto;
    color: #c8ffc8;
    scrollbar-size-vertical: 2;      /* Very thin scrollbar width */
    scrollbar-color: #1e3a3a;        /* Scrollbar thumb color */
    scrollbar-background: #0d1a0d;   /* Track color */
    scrollbar-color-hover: #2a4a4a;
    scrollbar-color-active: #00e5cc;
}

/* ── FOOTER ── */
Footer {
    background: #0d1a0d;
    color: #446666;
    height: 1;
}
Footer > .footer--key {
    background: #1a2e2e;
    color: #00e5cc;
}
Footer > .footer--highlight {
    background: #1e3a3a;
    color: #00ffff;
}

"""


# ══════════════════════════════════════════════════════════════════════════════
#  WIDGET: HistoryPanel
# ══════════════════════════════════════════════════════════════════════════════

MAX_HISTORY_ROWS = 8


# ══════════════════════════════════════════════════════════════════════════════
#  THE MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

class CliceOS(App):
    """CLICE OS terminal emulator with toggleable sidebar."""

    CSS = DEFAULT_CSS

    BINDINGS = [
        Binding("ctrl+q", "quit", "QUIT"),
        Binding("ctrl+s", "submit", "SUBMIT"),
        Binding("ctrl+d", "toggle_sidebar", "Challenge Info"),
        Binding("ctrl+h", "show_help", "HELP"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_challenge = CHALLENGES[0]  # For demo, use first challenge
        self.sidebar_visible = False

    # ── LAYOUT ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        """Build the main layout with terminal area and toggleable sidebar."""
        
        # Main horizontal layout (terminal + sidebar)
        with Horizontal(id="main-horizontal"):
            # Terminal area (always visible)
            with Vertical(id="terminal-area"):
                with ScrollableContainer(id="terminal-scroll"):
                    yield RichLog(id="output-log", highlight=False, markup=True)
                    with Horizontal(id="prompt-row"):
                        yield Static("[bold #00e5cc]user@clice:~$[/]", id="prompt-label")
                        yield Input(placeholder="", id="cmd-input")
            
            # Sidebar (hidden by default)
            with Vertical(id="sidebar"):
                yield Static("", id="sidebar-header")
                yield Markdown("", id="sidebar-content")
        
        yield Footer()

    def on_mount(self) -> None:
        """Print welcome banner and focus input."""
        log = self.query_one("#output-log", RichLog)
        log.write("[bold #00ffff]Welcome to CLICE Session Terminal[/]")
        log.write("[#446666]Kernel: Linux 5.15.0-x86_64-clice-runtime[/]")
        log.write("")

        # Prevent terminal widgets from stealing focus
        self.query_one("#output-log").can_focus = False
        self.query_one("#terminal-scroll").can_focus = False
        self.query_one("#terminal-area").can_focus = False
        self.query_one("#prompt-row").can_focus = False
        self.query_one("#prompt-label").can_focus = False

        self.query_one("#cmd-input", Input).focus()

    # ── SIDEBAR TOGGLE ─────────────────────────────────────────────────────────

    def action_toggle_sidebar(self) -> None:
        """Toggle the challenge info sidebar."""
        sidebar = self.query_one("#sidebar", Vertical)
        
        
        if self.sidebar_visible:
            # Hide sidebar
            sidebar.remove_class("visible")
            self.sidebar_visible = False
            # Return focus to input
            self.query_one("#cmd-input", Input).focus()
        else:
            # Populate sidebar with challenge info
            header = self.query_one("#sidebar-header", Static)
            content = self.query_one("#sidebar-content", Markdown)
            
            header.update(f"║ CHALLENGE: {self.current_challenge['id']} – {self.current_challenge['title']} ║")
            content.update(self.current_challenge.get("markdown", "_No description available._"))
            
            # Show sidebar
            sidebar.add_class("visible")
            # sidebar.can_focus = True
            self.sidebar_visible = True
            # Optionally focus the sidebar content for keyboard navigation
            content.focus()
    
    def on_key(self, event):
        if self.sidebar_visible and event.key == "escape":
            self.query_one("#cmd-input", Input).focus()
        if event.key == "ctrl+d":
            event.stop()  # Don't let it propagate
            self.action_toggle_sidebar()

    # ── COMMAND PROCESSOR ─────────────────────────────────────────────────────

    def _run_command(self, command: str) -> None:
        """Handle a command."""
        log = self.query_one("#output-log", RichLog)
        inp = self.query_one("#cmd-input", Input)
        scroller = self.query_one("#terminal-scroll", ScrollableContainer)

        # Write prompt + command to log
        log.write(f"[bold #00e5cc]user@clice:~$[/] [#f0fafa]{command}[/]")

        cmd = command.strip()

        if cmd == "":
            pass

        elif cmd in ("ls", "ls -la", "ls -l"):
            log.write("[#555555]total 12[/]")
            log.write("[#aaaaaa]drwxr-xr-x 3 user user 4096 Oct 24 14:19 [#c8ffc8].[/][/]")
            log.write("[#aaaaaa]drwxr-xr-x 3 root root 4096 Oct 24 14:18 [#c8ffc8]..[/][/]")
            log.write("[#aaaaaa]-rw-r--r-- 1 user user  220 Oct 24 14:18 [#c8ffc8].bash_logout[/][/]")

        elif cmd == "cat /etc/hosts":
            log.write("[#cccccc]127.0.0.1   [#00e5cc]localhost[/][/]")
            log.write("[#cccccc]::1         [#00e5cc]localhost[/] ip6-localhost[/]")
            log.write("[#cccccc]172.20.0.1  [#00ffff]clice-srv-01[/][/]")

        elif cmd in ("clear", "cls"):
            log.clear()

        elif cmd in ("exit", "quit"):
            self.exit()

        elif cmd == "help":
            log.write("[#00ffff]Available demo commands:[/]")
            log.write(f"  [#00e5cc]ls[/] [#666666]/ ls -la[/]       [#888888]list files[/]")
            log.write(f"  [#00e5cc]cat /etc/hosts[/]    [#888888]show hosts file[/]")
            log.write(f"  [#00e5cc]clear[/]             [#888888]wipe the screen[/]")
            log.write(f"  [#00e5cc]exit[/]              [#888888]quit the app[/]")

        else:
            log.write(
                f"[#ff4444]bash: {cmd.split()[0]}: command not found[/]"
                f"  [#555555](try 'help')[/]"
            )

        inp.value = ""
        scroller.scroll_end(animate=False)

    # ── ACTIONS ───────────────────────────────────────────────────────────────

    def action_submit(self) -> None:
        """Ctrl+S — run current input."""
        inp = self.query_one("#cmd-input", Input)
        if inp.value.strip():
            self._run_command(inp.value)

    def action_show_help(self) -> None:
        """Ctrl+H — show help."""
        self._run_command("help")

    # ── EVENT HANDLER ─────────────────────────────────────────────────────────

    @on(Input.Submitted, "#cmd-input")
    def handle_enter(self, event: Input.Submitted) -> None:
        """Enter key — run the command."""
        self._run_command(event.value)


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    CliceOS().run()
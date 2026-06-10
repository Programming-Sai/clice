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
from textual.widgets import Footer, TextArea, RichLog, Static, Markdown
from ui.screens.data.challenges import CHALLENGES
from textual.reactive import reactive


# ══════════════════════════════════════════════════════════════════════════════
#  WIDGET: TerminalInput
#  A TextArea that embeds the prompt as protected text, wraps naturally,
#  and aligns continuation lines with the input start (after the prompt).
# ══════════════════════════════════════════════════════════════════════════════

PROMPT = "user@clice:~$ "
PROMPT_LEN = len(PROMPT)


class TerminalInput(TextArea):
    """
    TextArea subclass that:
    - Embeds the prompt as non-deletable prefix text
    - Submits on Enter (no newline inserted)
    - Shift+Enter inserts a real newline for multiline commands
    - Blocks cursor from entering the prompt region
    - Up/Down navigate history
    """

    DEFAULT_CSS = """
    TerminalInput {
        width: 1fr;
        height: auto;
        min-height: 1;
        background: #0d0d0d;
        border: none;
        color: #f0fafa;
        padding: 0;
    }
    TerminalInput:focus {
        border: none;
        background: #0d0d0d;
    }
    TerminalInput > .text-area--cursor {
        background: #1a2e2e;
        color: #ffffff;
    }
    """

    def on_mount(self) -> None:
        self._reset()

    def _reset(self) -> None:
        """Load prompt and move cursor to after it."""
        self.load_text(PROMPT)
        self.move_cursor((0, PROMPT_LEN))

    def get_input(self) -> str:
        """Return only the user-typed portion."""
        lines = self.text.split("\n")
        # First line: strip prompt
        first = lines[0][PROMPT_LEN:] if lines[0].startswith(PROMPT) else lines[0]
        rest = lines[1:]
        return "\n".join([first] + rest)

    def _on_key(self, event) -> None:
        row, col = self.cursor_location

        # ── Enter: submit ──────────────────────────────────────────
        if event.key == "enter":
            event.prevent_default()
            event.stop()
            user_input = self.get_input().strip()
            self.app.handle_terminal_submit(user_input)
            return

        # ── Shift+Enter: real newline (multiline command) ──────────
        if event.key == "shift+enter":
            event.prevent_default()
            event.stop()
            self.insert("\n")
            return

        # ── Backspace: block if at or before prompt boundary ───────
        if event.key == "backspace":
            if row == 0 and col <= PROMPT_LEN:
                event.prevent_default()
                event.stop()
                return

        # ── Delete: block if cursor is inside prompt region ────────
        if event.key == "delete":
            if row == 0 and col < PROMPT_LEN:
                event.prevent_default()
                event.stop()
                return

        # ── Left arrow: block moving into prompt ───────────────────
        if event.key == "left":
            if row == 0 and col <= PROMPT_LEN:
                event.prevent_default()
                event.stop()
                return

        # ── Home: jump to after prompt, not start of line ──────────
        if event.key == "home":
            event.prevent_default()
            event.stop()
            if row == 0:
                self.move_cursor((0, PROMPT_LEN))
            else:
                self.move_cursor((row, 0))
            return

        # ── Up: history previous ───────────────────────────────────
        if event.key == "up":
            event.prevent_default()
            event.stop()
            self.app.action_history_up()
            return

        # ── Down: history next ─────────────────────────────────────
        if event.key == "down":
            event.prevent_default()
            event.stop()
            self.app.action_history_down()
            return

        super()._on_key(event)

    def action_select_all(self) -> None:
        """Override select-all to only select user input, not the prompt."""
        lines = self.text.split("\n")
        last_row = len(lines) - 1
        last_col = len(lines[-1])
        self.selection = ((0, PROMPT_LEN), (last_row, last_col))  # type: ignore

    def load_history(self, cmd: str) -> None:
        """Load a history entry, preserving the prompt."""
        self.load_text(PROMPT + cmd)
        line = self.text.split("\n")[0]
        self.move_cursor((0, len(line)))


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
}

/* ── SCROLLABLE TERMINAL AREA ── */
#terminal-scroll {
    #terminal-scroll {
    height: 1fr;
    overflow-y: auto;
    background: #0d0d0d;
    padding: 0 2;
    scrollbar-size-vertical: 1;    /* ← add this */
    scrollbar-color: #1e3a3a;
    scrollbar-background: #0d0d0d;
    scrollbar-color-hover: #2a4a4a;
    scrollbar-color-active: #00e5cc;
}
}

/* ── OUTPUT LOG ── */
#output-log {
    height: auto;
    background: #0d0d0d;
    overflow-x: hidden;
    overflow-y: hidden;    /* ← add this */
    border: none;
    padding: 0 1 0 0;
    color: #cccccc;
    scrollbar-size-vertical: 1;
}

/* ── PROMPT ROW ── */
#prompt-row {
    height: auto;
    layout: vertical;
    background: #0d0d0d;
    padding: 0;
}

/* ── SIDEBAR (RIGHT PANEL) ── */
#sidebar {
    display: none;
    background: #0d1a0d;
    border-left: solid #1e3a3a;
    padding: 1 2;
}

#sidebar.visible {
    display: block;
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
    scrollbar-size-vertical: 2;
    scrollbar-color: #1e3a3a;
    scrollbar-background: #0d1a0d;
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
#  THE MAIN APP
# ══════════════════════════════════════════════════════════════════════════════

MAX_HISTORY_ROWS = 8


class CliceOS(App):
    """CLICE OS terminal emulator with toggleable sidebar."""

    CSS = DEFAULT_CSS
    cmd_history: list[str] = []
    history_index: reactive[int] = reactive(-1)

    BINDINGS = [
        Binding("ctrl+q", "quit", "QUIT"),
        Binding("ctrl+s", "submit", "SUBMIT"),
        Binding("ctrl+d", "toggle_sidebar", "Challenge Info"),
        Binding("ctrl+h", "show_help", "HELP"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_challenge = CHALLENGES[0]
        self.sidebar_visible = False

    # ── LAYOUT ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        with Horizontal(id="main-horizontal"):
            with Vertical(id="terminal-area"):
                with ScrollableContainer(id="terminal-scroll"):
                    yield RichLog(id="output-log", highlight=False, markup=True, wrap=True)
                    with Vertical(id="prompt-row"):
                        yield TerminalInput(id="cmd-input")

            with Vertical(id="sidebar"):
                yield Static("", id="sidebar-header")
                yield Markdown("", id="sidebar-content")

        yield Footer()

    def on_resize(self, event) -> None:
        self.query_one("#output-log", RichLog).refresh()

    def on_mount(self) -> None:
        log = self.query_one("#output-log", RichLog)
        log.write("[bold #00ffff]Welcome to CLICE Session Terminal[/]")
        log.write("[#446666]Kernel: Linux 5.15.0-x86_64-clice-runtime[/]")
        log.write("")

        self.query_one("#output-log").can_focus = False
        self.query_one("#terminal-scroll").can_focus = False
        self.query_one("#terminal-area").can_focus = False
        self.query_one("#prompt-row").can_focus = False

        self.query_one("#cmd-input", TerminalInput).focus()

    # ── SIDEBAR TOGGLE ────────────────────────────────────────────────────────

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar", Vertical)

        if self.sidebar_visible:
            sidebar.remove_class("visible")
            self.sidebar_visible = False
            self.query_one("#cmd-input", TerminalInput).focus()
        else:
            header = self.query_one("#sidebar-header", Static)
            content = self.query_one("#sidebar-content", Markdown)
            header.update(f"║ CHALLENGE: {self.current_challenge['id']} – {self.current_challenge['title']} ║")
            content.update(self.current_challenge.get("markdown", "_No description available._"))
            sidebar.add_class("visible")
            self.sidebar_visible = True
            content.focus()

    # ── KEY HANDLER ───────────────────────────────────────────────────────────

    def on_key(self, event) -> None:
        if self.sidebar_visible and event.key == "escape":
            self.query_one("#cmd-input", TerminalInput).focus()

        if event.key == "ctrl+d":
            event.stop()
            self.action_toggle_sidebar()

        if event.key == "ctrl+c":
            event.stop()
            if hasattr(self, "command_running") and self.command_running:
                self.shell_session.send_intr()
                self.command_running = False
            log = self.query_one("#output-log", RichLog)
            log.write("[bold #00e5cc]user@clice:~$[/] ^C")

    # ── HISTORY ───────────────────────────────────────────────────────────────

    def action_history_up(self) -> None:
        inp = self.query_one("#cmd-input", TerminalInput)
        scroller = self.query_one("#terminal-scroll", ScrollableContainer)
        if self.history_index < len(self.cmd_history) - 1:
            self.history_index += 1
            cmd = self.cmd_history[len(self.cmd_history) - 1 - self.history_index]
            inp.load_history(cmd)
        scroller.scroll_end(animate=False)    # ← add this

    def action_history_down(self) -> None:
        inp = self.query_one("#cmd-input", TerminalInput)
        scroller = self.query_one("#terminal-scroll", ScrollableContainer)
        if self.history_index > -1:
            self.history_index -= 1
            if self.history_index >= 0:
                cmd = self.cmd_history[len(self.cmd_history) - 1 - self.history_index]
                inp.load_history(cmd)
            else:
                inp._reset()
        scroller.scroll_end(animate=False)    # ← add this

    # ── SUBMISSION ────────────────────────────────────────────────────────────

    def handle_terminal_submit(self, command: str) -> None:
        """Called by TerminalInput on Enter."""
        self._run_command(command)

    def action_submit(self) -> None:
        """Ctrl+S — submit current input."""
        inp = self.query_one("#cmd-input", TerminalInput)
        self._run_command(inp.get_input().strip())

    # ── COMMAND PROCESSOR ─────────────────────────────────────────────────────

    def _run_command(self, command: str) -> None:
        log = self.query_one("#output-log", RichLog)
        inp = self.query_one("#cmd-input", TerminalInput)
        scroller = self.query_one("#terminal-scroll", ScrollableContainer)

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

        elif cmd.startswith("echo "):
            log.write(cmd[5:])

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

        if cmd != "":
            self.cmd_history.append(cmd)
        self.history_index = -1
        inp._reset()
        scroller.scroll_end(animate=False)

    # ── ACTIONS ───────────────────────────────────────────────────────────────

    def action_show_help(self) -> None:
        self._run_command("help")


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    CliceOS().run()
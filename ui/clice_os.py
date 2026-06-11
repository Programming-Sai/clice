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
#  PROMPT CONFIG
# ══════════════════════════════════════════════════════════════════════════════

PROMPT_TEXT = "user@clice:/mnt/hello/workspace~$ "
PROMPT_PAD  = " " * len(PROMPT_TEXT)
PROMPT_LEN  = len(PROMPT_TEXT)


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
        color: #446666;
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
            " [bold #1a2e2e on #1a2e2e] ^Q [/][#446666] QUIT [/]"
            "[bold #1a2e2e on #1a2e2e] ^S [/][#446666] SUBMIT [/]"
            "[bold #1a2e2e on #1a2e2e] ^D [/][#446666] CHALLENGE [/]"
            "[bold #1a2e2e on #1a2e2e] ^H [/][#446666] HELP [/]"
            "[bold #1a2e2e on #1a2e2e] ^L [/][#446666] CLEAR [/]"
            "[bold #1a2e2e on #1a2e2e] ^T [/][#446666] TIMER [/]",
            id="footer-keys"
        )
        yield Static("", id="footer-timer")


# ══════════════════════════════════════════════════════════════════════════════
#  WIDGET: TerminalInput
# ══════════════════════════════════════════════════════════════════════════════

class TerminalInput(TextArea):
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
        self.load_text(PROMPT_PAD)
        self.move_cursor((0, PROMPT_LEN))

    def get_input(self) -> str:
        lines = self.text.split("\n")
        first = lines[0][PROMPT_LEN:]
        rest = lines[1:]
        return "\n".join([first] + rest).strip()

    def _on_key(self, event) -> None:
        row, col = self.cursor_location
        
        if event.key == "shift+enter":
            event.prevent_default()
            event.stop()
            self.insert("\n")
            return
        
        if event.key == "enter":
            event.prevent_default()
            event.stop()
            self.app.handle_terminal_submit(self.get_input())
            return

        if event.key == "backspace":
            if row == 0 and col <= PROMPT_LEN:
                event.prevent_default()
                event.stop()
                return

        if event.key == "delete":
            if row == 0 and col < PROMPT_LEN:
                event.prevent_default()
                event.stop()
                return

        if event.key == "left":
            if row == 0 and col <= PROMPT_LEN:
                event.prevent_default()
                event.stop()
                return

        if event.key == "home":
            event.prevent_default()
            event.stop()
            if row == 0:
                self.move_cursor((0, PROMPT_LEN))
            else:
                self.move_cursor((row, 0))
            return

        if event.key == "ctrl+a":
            event.prevent_default()
            event.stop()
            self.move_cursor((0, PROMPT_LEN))
            return

        if event.key == "ctrl+u":
            event.prevent_default()
            event.stop()
            self._reset()
            return

        if event.key == "ctrl+w":
            event.prevent_default()
            event.stop()
            row, col = self.cursor_location
            min_col = PROMPT_LEN if row == 0 else 0
            line = self.text.split("\n")[row]
            before = line[:col].rstrip()
            last_space = before.rfind(" ")
            target_col = max(last_space + 1, min_col) if last_space >= 0 else min_col
            if target_col < col:
                self.move_cursor((row, target_col))
                self.delete((row, target_col), (row, col))
            return

        if event.key == "up":
            event.prevent_default()
            event.stop()
            self.app.action_history_up()
            return

        if event.key == "down":
            event.prevent_default()
            event.stop()
            self.app.action_history_down()
            return


        super()._on_key(event)

    def action_select_all(self) -> None:
        lines = self.text.split("\n")
        last_row = len(lines) - 1
        last_col = len(lines[-1])
        self.selection = ((0, PROMPT_LEN), (last_row, last_col))  # type: ignore

    def load_history(self, cmd: str) -> None:
        self.load_text(PROMPT_PAD + cmd)
        lines = self.text.split("\n")
        last_row = len(lines) - 1
        self.move_cursor((last_row, len(lines[-1])))

    def on_paste(self, event) -> None:
        self.app.query_one("#terminal-scroll", ScrollableContainer).scroll_end(animate=False)

    def on_click(self, event) -> None:
        self.call_after_refresh(self._guard_cursor)

    def _guard_cursor(self) -> None:
        row, col = self.cursor_location
        if row == 0 and col < PROMPT_LEN:
            self.move_cursor((0, PROMPT_LEN))


# ─── CSS ──────────────────────────────────────────────────────────────────────
DEFAULT_CSS = """
Screen {
    background: #0a0a0a;
    color: #c8ffc8;
    layout: vertical;
}

#main-horizontal {
    height: 1fr;
    layout: horizontal;
}

#terminal-area {
    width: 1fr;
    layout: vertical;
    background: #0a0a0a;
}

#terminal-scroll {
    height: 1fr;
    overflow-y: auto;
    background: #0d0d0d;
    padding: 0 2;
    scrollbar-size-vertical: 1;
    scrollbar-color: #1e3a3a;
    scrollbar-background: #0d0d0d;
    scrollbar-color-hover: #2a4a4a;
    scrollbar-color-active: #00e5cc;
}

#output-log {
    height: auto;
    background: #0d0d0d;
    overflow-x: hidden;
    overflow-y: hidden;
    border: none;
    padding: 0 1 0 0;
    color: #cccccc;
    scrollbar-size-vertical: 1;
}

#prompt-row {
    height: auto;
    layout: horizontal;
    background: #0d0d0d;
    padding: 0;
    layers: above;
}

#prompt-label {
    layer: above;
    offset: 0 0;
    width: auto;
    height: 1;
    color: #00e5cc;
    text-style: bold;
    background: #0d0d0d;
    padding: 0;
    dock: left;
}

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
    scrollbar-size-vertical: 1;
    scrollbar-color: #1e3a3a;
    scrollbar-background: #0d1a0d;
    scrollbar-color-hover: #2a4a4a;
    scrollbar-color-active: #00e5cc;
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
        Binding("ctrl+l", "clear_log", "CLEAR"),
        Binding("ctrl+t", "toggle_timer", "Timer"),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_challenge = CHALLENGES[0]
        self.sidebar_visible = False
        self.timer_visible = False
        self._timer = None

    # ── LAYOUT ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        with Horizontal(id="main-horizontal"):
            with Vertical(id="terminal-area"):
                with ScrollableContainer(id="terminal-scroll"):
                    yield RichLog(id="output-log", highlight=False, markup=True, wrap=True)
                    with Horizontal(id="prompt-row"):
                        yield Static(PROMPT_TEXT, id="prompt-label")
                        yield TerminalInput(id="cmd-input")

            with Vertical(id="sidebar"):
                yield Static("", id="sidebar-header")
                yield Markdown("", id="sidebar-content")

        yield AppFooter()

    def on_resize(self, event) -> None:
        log = self.query_one("#output-log", RichLog)
        scroller = self.query_one("#terminal-scroll", ScrollableContainer)
        log.refresh(layout=True)
        self.call_after_refresh(scroller.scroll_end, animate=False)

    def _update_prompt_width(self) -> None:
        label = self.query_one("#prompt-label", Static)
        label.styles.width = PROMPT_LEN

    def on_mount(self) -> None:
        self.query_one("#output-log").can_focus = False
        self.query_one("#terminal-scroll").can_focus = False
        self.query_one("#terminal-area").can_focus = False
        self.query_one("#prompt-row").can_focus = False
        self.query_one("#prompt-label").can_focus = False
        self._update_prompt_width()
        self.query_one("#cmd-input", TerminalInput).focus()
        self.call_after_refresh(self._write_welcome)

    def _write_welcome(self) -> None:
        log = self.query_one("#output-log", RichLog)
        log.write("[bold #00ffff]Welcome to CLICE Session Terminal[/]")
        log.write("[#446666]Kernel: Linux 5.15.0-x86_64-clice-runtime[/]")
        log.write("")
        self.query_one("#terminal-scroll", ScrollableContainer).scroll_end(animate=False)

    # ── SIDEBAR TOGGLE ────────────────────────────────────────────────────────

    def action_toggle_sidebar(self) -> None:
        sidebar = self.query_one("#sidebar", Vertical)

        if self.sidebar_visible:
            sidebar.remove_class("visible")
            self.sidebar_visible = False
            self.query_one("#cmd-input", TerminalInput).focus()
            self.notify("Challenge info hidden", timeout=1.5)
        else:
            header = self.query_one("#sidebar-header", Static)
            content = self.query_one("#sidebar-content", Markdown)
            header.update(f"║ CHALLENGE: {self.current_challenge['id']} – {self.current_challenge['title']} ║")
            content.update(self.current_challenge.get("markdown", "_No description available._"))
            sidebar.add_class("visible")
            self.sidebar_visible = True
            content.focus()
            self.notify("Challenge info shown", timeout=1.5)

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
            log.write(f"[bold #00e5cc]{PROMPT_TEXT}[/] ^C")

        # elif "ctrl+" in event.key:
        #     event.stop()
        #     if hasattr(self, "command_running") and self.command_running:
        #         self.shell_session.send_intr()
        #         self.command_running = False
        #     log = self.query_one("#output-log", RichLog)
        #     log.write(f"[bold #00e5cc]{PROMPT_TEXT}[/] {event.key.replace("ctrl+", "^").upper()}")

    # ── HISTORY ───────────────────────────────────────────────────────────────

    def action_history_up(self) -> None:
        inp = self.query_one("#cmd-input", TerminalInput)
        scroller = self.query_one("#terminal-scroll", ScrollableContainer)
        if self.history_index < len(self.cmd_history) - 1:
            self.history_index += 1
            cmd = self.cmd_history[len(self.cmd_history) - 1 - self.history_index]
            inp.load_history(cmd)
        scroller.scroll_end(animate=False)

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
        scroller.scroll_end(animate=False)

    # ── SUBMISSION ────────────────────────────────────────────────────────────

    def handle_terminal_submit(self, command: str) -> None:
        self._run_command(command)

    def action_submit(self) -> None:
        inp = self.query_one("#cmd-input", TerminalInput)
        self._run_command(inp.get_input().strip())

    # ── COMMAND PROCESSOR ─────────────────────────────────────────────────────

    def _run_command(self, command: str) -> None:
        log = self.query_one("#output-log", RichLog)
        inp = self.query_one("#cmd-input", TerminalInput)
        scroller = self.query_one("#terminal-scroll", ScrollableContainer)

        log.write(f"[bold #00e5cc]{PROMPT_TEXT}[/][#f0fafa]{command}[/]")

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

    def action_clear_log(self) -> None:
        self.query_one("#output-log", RichLog).clear()
        self.query_one("#cmd-input", TerminalInput).focus()
        self.notify("Screen cleared", timeout=1.5)

    def action_toggle_timer(self) -> None:
        display = self.query_one("#footer-timer", Static)
        if self.timer_visible:
            display.remove_class("visible")
            if self._timer:
                self._timer.stop()
            self.timer_visible = False
            self.notify("Timer OFF", timeout=1.5)
        else:
            display.add_class("visible")
            self._timer = self.set_interval(1, self._tick_timer)
            self.timer_visible = True
            self._tick_timer()  # show immediately, don't wait 1s
            self.notify("Timer ON", timeout=1.5)

    def _tick_timer(self) -> None:
        display = self.query_one("#footer-timer", Static)
        now = datetime.now().strftime("%H:%M:%S")
        display.update(f"[#446666]──[/] [#00e5cc]{now}[/]")


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    CliceOS().run()
"""
CLICE_OS Terminal UI — built with Python Textual
=================================================
"""

from pathlib import Path
from datetime import datetime

from textual.screen import Screen
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import RichLog, Static, Markdown
from textual.reactive import reactive
from ui.widgets.session.app_footer import AppFooter
from ui.widgets.session.prompt_config import PROMPT_LEN, PROMPT_TEXT
from ui.widgets.session.terminal_input import TerminalInput







class SessionScreen(Screen):
    """Live terminal session for a challenge."""

    CSS_PATH = Path(__file__).parent / "session.tcss"
    cmd_history: list[str] = []
    history_index: reactive[int] = reactive(-1)

    BINDINGS = [
        Binding("ctrl+q", "quit", "QUIT"),
        Binding("ctrl+s", "submit", "SUBMIT"),
        Binding("ctrl+d", "toggle_sidebar", "Challenge Info"),
        Binding("ctrl+h", "show_help", "HELP"),
        Binding("ctrl+l", "clear_log", "CLEAR"),
        Binding("ctrl+t", "toggle_timer", "Timer"),
        Binding("escape", "app.pop_screen", "BACK", show=True),
    ]

    def __init__(self, challenge:dict, sidebar_visible:bool, timer_visible:bool , **kwargs):
        super().__init__(**kwargs)
        self.current_challenge = challenge
        self.sidebar_visible = sidebar_visible
        self.timer_visible = timer_visible
        self._timer = None
        self.session_start_time = None 

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
        self.session_start_time = datetime.now()
        if self.sidebar_visible:
            self.sidebar_visible = False  # reset so toggle flips it open correctly
            self.call_after_refresh(self.action_toggle_sidebar)
        if self.timer_visible:
            self.timer_visible = False  # reset so toggle flips it open correctly
            self.call_after_refresh(self.action_toggle_timer)
        

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
            # self.notify("Challenge info hidden", timeout=1.5)
        else:
            header = self.query_one("#sidebar-header", Static)
            content = self.query_one("#sidebar-content", Markdown)
            header.update(f"║ CHALLENGE: {self.current_challenge['id']} – {self.current_challenge['title']} ║")
            content.update(self.current_challenge.get("markdown", "_No description available._"))
            sidebar.add_class("visible")
            self.sidebar_visible = True
            content.focus()
            # self.notify("Challenge info shown", timeout=1.5)

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
        # self.notify("Screen cleared", timeout=1.5)

    def action_toggle_timer(self) -> None:
        display = self.query_one("#footer-timer", Static)
        if self.timer_visible:
            display.remove_class("visible")
            if self._timer:
                self._timer.stop()
            self.timer_visible = False
            # self.notify("Timer OFF", timeout=1.5)
        else:
            display.add_class("visible")
            self._timer = self.set_interval(1, self._tick_timer)
            self.timer_visible = True
            self._tick_timer()  # show immediately, don't wait 1s
            # self.notify("Timer ON", timeout=1.5)

    def _tick_timer(self) -> None:
        display = self.query_one("#footer-timer", Static)
        if self.session_start_time:
            elapsed = datetime.now() - self.session_start_time
            # Format as HH:MM:SS or MM:SS
            total_seconds = int(elapsed.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            display.update(f"[#446666]──[/] [#00e5cc]{time_str}[/]")
        else:
            # Fallback to clock time if session not started
            now = datetime.now().strftime("%H:%M:%S")
            display.update(f"[#446666]──[/] [#00e5cc]{now}[/]")


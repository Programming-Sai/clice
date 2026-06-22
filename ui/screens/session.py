"""
CLICE_OS Terminal UI — Session Screen
======================================
Live terminal session for a challenge.
"""

from pathlib import Path
from datetime import datetime
from textual.screen import Screen
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import RichLog, Static, Markdown
from textual.reactive import reactive
from ui.screens.verdict import VerdictScreen
from ui.widgets.footer import Footer
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

    def __init__(self, challenge: dict, sidebar_visible: bool, timer_visible: bool, **kwargs):
        super().__init__(**kwargs)
        self.current_challenge = challenge
        self.sidebar_visible = sidebar_visible
        self.timer_visible = timer_visible  # initial state
        self._timer_interval = None
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
        yield Footer()

    def on_resize(self, event) -> None:
        log = self.query_one("#output-log", RichLog)
        scroller = self.query_one("#terminal-scroll", ScrollableContainer)
        log.refresh(layout=True)
        self.call_after_refresh(scroller.scroll_end, animate=False)

    def _update_prompt_width(self) -> None:
        label = self.query_one("#prompt-label", Static)
        label.styles.width = PROMPT_LEN

    def on_mount(self) -> None:
        # ── Set footer context ────────────────────────────────────────────────
        self.query_one(Footer).set_screen("session")

        # ── Prevent focus stealing ────────────────────────────────────────────
        self.query_one("#output-log").can_focus = False
        self.query_one("#terminal-scroll").can_focus = False
        self.query_one("#terminal-area").can_focus = False
        self.query_one("#prompt-row").can_focus = False
        self.query_one("#prompt-label").can_focus = False
        self._update_prompt_width()

        # ── Focus input ────────────────────────────────────────────────────────
        self.query_one("#cmd-input", TerminalInput).focus()

        # ── Welcome message ────────────────────────────────────────────────────
        self.call_after_refresh(self._write_welcome)

        # ── Session start time ────────────────────────────────────────────────
        self.session_start_time = datetime.now()

        # ── Sidebar ────────────────────────────────────────────────────────────
        if self.sidebar_visible:
            self.sidebar_visible = False
            self.call_after_refresh(self.action_toggle_sidebar)

        # ── Timer ──────────────────────────────────────────────────────────────
        if self.timer_visible:
            self._start_timer()
        else:
            self.query_one(Footer).set_right_content("")

    def _write_welcome(self) -> None:
        log = self.query_one("#output-log", RichLog)
        log.write("[bold #00ffff]Welcome to CLICE Session Terminal[/]")
        log.write("[#446666]Kernel: Linux 5.15.0-x86_64-clice-runtime[/]")
        log.write("")
        self.query_one("#terminal-scroll", ScrollableContainer).scroll_end(animate=False)

    # ── SIDEBAR ────────────────────────────────────────────────────────────────

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
            log.write(f"[bold #00e5cc]{PROMPT_TEXT}[/] ^C")

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
        """Submit the session and show verdict."""
        import random
        goal_reached = random.choice([True, False])

        log_data = {
            "challenge_id": self.current_challenge["id"],
            "started_at": self.session_start_time.isoformat() if self.session_start_time else datetime.now().isoformat(),
            "submitted_at": datetime.now().isoformat(),
            "goal_reached": goal_reached,
            "commands": [{"command": c, "timestamp": "", "exit_code": 0} for c in self.cmd_history]
        }

        # Stop timer before pushing verdict
        self._stop_timer()
        self.query_one(Footer).set_right_content("")

        self.app.push_screen(VerdictScreen(self.current_challenge, log_data))

    # ── TIMER ──────────────────────────────────────────────────────────────────

    def _start_timer(self) -> None:
        """Start the timer update interval."""
        if not self._timer_interval:
            self._timer_interval = self.set_interval(1, self._update_footer_timer)
            self._update_footer_timer()  # show immediately
            self.timer_visible = True

    def _stop_timer(self, update_footer: bool = True) -> None:
        """Stop the timer update interval."""
        if self._timer_interval:
            self._timer_interval.stop()
            self._timer_interval = None
        if update_footer:
            try:
                self.query_one(Footer).set_right_content("")
            except:
                pass  # Footer may already be gone
        self.timer_visible = False

    def _update_footer_timer(self) -> None:
        """Update the timer in the global footer."""
        if not self.timer_visible or not self.session_start_time:
            return

        elapsed = datetime.now() - self.session_start_time
        total_seconds = int(elapsed.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.query_one(Footer).set_right_content(f"TIMER: {time_str}")

    def action_toggle_timer(self) -> None:
        """Toggle timer display on/off."""
        if self.timer_visible:
            self._stop_timer()
        else:
            self._start_timer()

    # ── COMMAND PROCESSOR ─────────────────────────────────────────────────────

    def _run_command(self, command: str) -> None:
        log = self.query_one("#output-log", RichLog)
        inp = self.query_one("#cmd-input", TerminalInput)
        scroller = self.query_one("#terminal-scroll", ScrollableContainer)

        log.write(f"[bold #00e5cc]{PROMPT_TEXT}[/][#f0fafa]{command}[/]")

        cmd = command.strip()

        if cmd == "":
            pass

        elif cmd == ":submit":
            self.action_submit()

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

    def action_quit(self) -> None:
        self._stop_timer(update_footer=False)
        self.app.pop_screen()

    def on_unmount(self) -> None:
        """Clean up timer when screen is popped."""
        self._stop_timer(update_footer=False)
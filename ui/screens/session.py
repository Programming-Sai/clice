"""
CLICE_OS Terminal UI — Session Screen
======================================
Live terminal session for a challenge.
"""

from pathlib import Path
from datetime import datetime
import threading

from textual import work
from logger.session import ShellSession
from logger.debug import trace
from textual.screen import Screen
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.widgets import RichLog, Static, Markdown
from textual.reactive import reactive
from ui.screens.verdict import VerdictScreen
from ui.widgets.footer import Footer
from ui.widgets.loading_overlay import LoadingOverlay
from ui.widgets.session.prompt_config import PROMPT_LEN, PROMPT_TEXT
from ui.widgets.session.terminal_input import TerminalInput
from verifier.check_runner import CheckRunner


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

    def __init__(self, challenge: dict, sidebar_visible: bool, timer_visible: bool, container=None, container_name=None,  loader=None, **kwargs):
        super().__init__(**kwargs)
        self.current_challenge = challenge
        self.sidebar_visible = sidebar_visible
        self.timer_visible = timer_visible
        self._timer_interval = None
        self.session_start_time = None
        self.container = container
        if container and hasattr(container, 'name'):
            self.container_name = container.name
        else:
            self.container_name = None
        self.shell_session = None
        self.loading_overlay = None
        self.loader = loader
        self.volume_name = loader.volume_name if loader else None
        trace("screen_init", challenge_id=challenge.get("id"), container_name=getattr(container, "name", None))

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
        
        self.loading_overlay = LoadingOverlay()
        yield self.loading_overlay

    def on_resize(self, event) -> None:
        log = self.query_one("#output-log", RichLog)
        scroller = self.query_one("#terminal-scroll", ScrollableContainer)
        log.refresh(layout=True)
        self.call_after_refresh(scroller.scroll_end, animate=False)

    def _update_prompt_width(self) -> None:
        label = self.query_one("#prompt-label", Static)
        label.styles.width = PROMPT_LEN

    def on_mount(self) -> None:
        trace("screen_on_mount", challenge_id=self.current_challenge.get("id"), container_name=self.container_name)
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
        self.query_one("#cmd-input", TerminalInput).disabled = True

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
        
        # ── Start shell session ────────────────────────────────────────────────
        self._start_shell_session()

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
            header.update(f"║ CHALLENGE: {self.current_challenge['code']} – {self.current_challenge['title']} ║")
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
        history = self.shell_session.commands if self.shell_session else []
        if self.history_index < len(history) - 1:
            self.history_index += 1
            history_item = history[len(history) - 1 - self.history_index]
            inp.load_history(history_item["command"])
        scroller.scroll_end(animate=False)

    def action_history_down(self) -> None:
        inp = self.query_one("#cmd-input", TerminalInput)
        scroller = self.query_one("#terminal-scroll", ScrollableContainer)
        history = self.shell_session.commands if self.shell_session else []
        if self.history_index > -1:
            self.history_index -= 1
            if self.history_index >= 0:
                history_item = history[len(history) - 1 - self.history_index]
                inp.load_history(history_item["command"])
            else:
                inp._reset()
        scroller.scroll_end(animate=False)

    # ── SUBMISSION ────────────────────────────────────────────────────────────

    def handle_terminal_submit(self, command: str) -> None:
        self._run_command(command)

    def action_submit(self) -> None:
            trace("session_action_submit_begin")
            self._stop_timer()
            self.query_one(Footer).set_right_content("")
            self.loading_overlay.show("Verifying challenge...")
            self._do_verify()  # kick off the worker

    @work(thread=True, exclusive=True)
    def _do_verify(self) -> None:
        trace("verify_thread_entered")
        try:
            trace("verify_before_shell_submit")
            log_data = self.shell_session.submit()
            trace("verify_after_shell_submit")
            log_data["challenge_id"] = self.current_challenge["id"]

            self.app.call_from_thread(self.loading_overlay.show, "Running verification checks...")
            trace("verify_before_loader_verify")

            loader = self.loader
            trace("verify_loader_check", has_loader=bool(loader), loader_id=id(loader) if loader else None, volume_name=self.volume_name)
            if not loader:
                trace("verify_loader_fallback_triggered")
                from loader.challenge_loader import ChallengeLoader
                loader = ChallengeLoader()
                loader.volume_name = self.volume_name

            trace("verify_checker_images_keys", keys=list(loader.checker_images.keys()))

            goal_reached = loader.verify(self.current_challenge["id"], self.container)
            trace("verify_after_loader_verify", goal_reached=goal_reached)
            log_data["goal_reached"] = goal_reached

            if self.loader and self.container:
                try:
                    self.loader.cleanup(self.container)
                    trace("verify_cleanup_done")
                except Exception as e:
                    trace("session_container_cleanup_error", error=repr(e))

            self.app.call_from_thread(self._show_verdict, log_data)
            trace("verify_show_verdict_called")

        except Exception as e:
            trace("verify_thread_exception", error=repr(e))
            self.app.call_from_thread(self._show_verdict_error, str(e))
    
    def _show_verdict(self, log_data: dict) -> None:
        trace("session_show_verdict_ui")
        self.loading_overlay.hide()
        self.app.push_screen(VerdictScreen(self.current_challenge, log_data))
        # SessionScreen stays on the stack underneath — do NOT pop it here
    
    def _show_verdict_error(self, error: str) -> None:
        """Show error if verification fails."""
        self.loading_overlay.hide()
        self.notify(f"Verification failed: {error}", title="Error", severity="error")
    
    # ── TIMER ──────────────────────────────────────────────────────────────────

    def _start_timer(self) -> None:
        if not self._timer_interval:
            self._timer_interval = self.set_interval(1, self._update_footer_timer)
            self._update_footer_timer()
            self.timer_visible = True

    def _stop_timer(self, update_footer: bool = True) -> None:
        if self._timer_interval:
            self._timer_interval.stop()
            self._timer_interval = None
        if update_footer:
            try:
                self.query_one(Footer).set_right_content("")
            except:
                pass
        self.timer_visible = False

    def _update_footer_timer(self) -> None:
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
        if self.timer_visible:
            self._stop_timer()
        else:
            self._start_timer()

    # ── SHELL SESSION ─────────────────────────────────────────────────────────

    def _start_shell_session(self) -> None:
        """Start the shell session with a loading overlay."""
        trace("screen_start_shell_begin", challenge_id=self.current_challenge.get("id"), container_name=self.container_name)
        self.loading_overlay.show("Starting shell session...")

        def load():
            try:
                trace("screen_shell_thread_begin", challenge_id=self.current_challenge.get("id"), container_name=self.container_name)
                # Run the shell session in this background thread so the UI stays responsive.
                shell = ShellSession(
                    challenge_id=self.current_challenge["id"],
                    container_name=self.container_name
                )
                trace("screen_shell_ipc_created")
                shell.start()
                trace("screen_shell_ipc_started")
                self.shell_session = shell
                self.app.call_from_thread(self._on_shell_ready)
            except Exception as e:
                trace("screen_shell_thread_error", error=repr(e))
                self.app.call_from_thread(self._on_shell_error, e)

        threading.Thread(target=load, daemon=True).start()
        trace("screen_shell_thread_spawned")

    def _on_shell_ready(self) -> None:
        trace("screen_shell_ready_ui")
        self.loading_overlay.hide()
        cmd_input = self.query_one("#cmd-input", TerminalInput)
        cmd_input.disabled = False
        self.session_start_time = datetime.now()
        self._write_welcome()
        cmd_input.focus()
        self._start_timer()

    def _on_shell_error(self, error: Exception) -> None:
        trace("screen_shell_error_ui", error=repr(error))
        self.loading_overlay.hide()
        self.notify(f"Failed to start shell: {error}", title="Error", severity="error")
        # input stays disabled — shell_session is still None, so _run_command's
        # existing "Shell not initialized" fallback won't silently swap to demo mode
        # unexpectedly; consider adding a retry binding here later.

    # ── COMMAND PROCESSOR ─────────────────────────────────────────────────────

    def _run_command(self, command: str) -> None:
        log = self.query_one("#output-log", RichLog)
        inp = self.query_one("#cmd-input", TerminalInput)
        scroller = self.query_one("#terminal-scroll", ScrollableContainer)

        cmd = command.strip()

        # Internal commands (not sent to shell)
        # if cmd == "":
        #     return
        if cmd == ":submit":
        # elif cmd == ":submit":
            self.action_submit()
            return
        elif cmd in ("exit", "quit"):
            log.write(f"[#888888]Closing session...[/]")
            if self.shell_session:
                self.shell_session.terminate()
            self.app.pop_screen()
            return
        elif cmd in ("clear", "cls"):
            log.clear()
            inp._reset()
            scroller.scroll_end(animate=False)
            return

        # ── REAL SHELL EXECUTION ────────────────────────────────────────────────
        if self.shell_session:
            try:
                # Write the command to the log
                log.write(f"[bold #00e5cc]{PROMPT_TEXT}[/][#f0fafa]{command}[/]")
                
                # Execute via shell
                output, exit_code, elapsed = self.shell_session.execute(cmd)
                
                # Display output
                if output:
                    log.write(output)
                
                # # Show exit code and timing
                # if exit_code == 0x:
                #     log.write(f"✓ [{elapsed:.2f}s]")
                # else:
                #     log.write(f"✗ [{elapsed:.2f}s] (exit: {exit_code})")
                
                # Store command in history
                self.cmd_history.append({
                    "command": cmd,
                    "output": output,
                    "exit_code": exit_code,
                    "elapsed": elapsed,
                    "timestamp": datetime.now().isoformat(),
                })
                self.history_index = -1
            except Exception as e:
                log.write(f"[#ff4444]Error: {e}[/]")
        else:
            # Fallback: demo mode (if shell isn't initialized)
            log.write(f"[#ff4444]Shell not initialized. Running in demo mode.[/]")
            self._demo_execute(cmd, log)

        inp._reset()
        scroller.scroll_end(animate=False)


    def _demo_execute(self, cmd: str, log) -> None:
        """Fallback demo commands when shell is not initialized."""

        if cmd in ("ls", "ls -la", "ls -l", "ls -a"):
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
        if self.shell_session:
            try:
                self.shell_session.terminate()
            except Exception as e:
                trace("session_unmount_shell_close_error", error=repr(e))

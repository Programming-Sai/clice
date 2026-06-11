
from textual.containers import ScrollableContainer
from textual.widgets import TextArea
from ui.widgets.session.prompt_config import PROMPT_LEN, PROMPT_PAD
from textual.widgets.text_area import TextAreaTheme




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
    """

    def on_mount(self) -> None:
        self._reset()
        theme = TextAreaTheme(
            name="clice",
            cursor_style="bold white on #00e5cc",
        )
        self.register_theme(theme)
        self.theme = "clice"

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
            self.screen.handle_terminal_submit(self.get_input())
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
            self.screen.action_history_up()
            return

        if event.key == "down":
            event.prevent_default()
            event.stop()
            self.screen.action_history_down()
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
        self.screen.query_one("#terminal-scroll", ScrollableContainer).scroll_end(animate=False)

    def on_click(self, event) -> None:
        self.call_after_refresh(self._guard_cursor)

    def _guard_cursor(self) -> None:
        row, col = self.cursor_location
        if row == 0 and col < PROMPT_LEN:
            self.move_cursor((0, PROMPT_LEN))

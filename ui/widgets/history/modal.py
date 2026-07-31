from textual.app import App, ComposeResult          # App = the whole program. ComposeResult = the list of widgets we build.
from textual.containers import Horizontal, Vertical  # Boxes that line widgets up in a row, or stack them up.
from textual.widgets import Static, DataTable, Input  # Static = plain text. DataTable = a spreadsheet-like grid.
from textual.screen import ModalScreen                # ModalScreen = a little popup window that floats on top.
from textual.binding import Binding                   # Binding = "when this key is pressed, run this action."
from ui.widgets.footer import Footer


# ---------------------------------------------------------------------------
# STEP 5.5: THE "ARE YOU SURE?" POPUP
# ---------------------------------------------------------------------------
# This is a "ModalScreen." Think of it like a little pop-up window that
# floats ON TOP of everything else and grabs all the keyboard's attention
# until you answer it. We use it any time we're about to do something we
# CAN'T UNDO, like deleting a row - so a stray key press can't accidentally
# wipe something out.
class ConfirmModal(ModalScreen[bool]):
    """
    A small "are you sure?" popup. It shows a message and waits for the
    person to press Y (yes) or N / Escape (no).

    The [bool] after ModalScreen means "when this popup closes, it hands
    back either True or False" - True for yes, False for no. Whoever
    opened the popup gets to react to that answer (see action_delete_row
    and action_clear_all below).
    """

    DEFAULT_CSS = """
    ConfirmModal {
        align: center middle;   /* puts our little box right in the middle of the screen */
        background: #131313 60%; /* a see-through dark overlay behind the popup */
    }

    #confirm_box {
        width: 64;
        height: auto;
        border: solid #005f5f;   /* same teal border style as the rest of the app */
        background: #131313;
        padding: 1 2;
    }

    #confirm_message {
        color: #c8d3d9;
        width: 1fr;
        content-align: center middle;
        padding-bottom: 1;
    }

    #confirm_buttons {
        width: 1fr;
        height: 1;
        align: center middle;
    }

    #confirm_yes {
        color: #4ade80;         /* green, like our PASS badges */
        width: auto;
        margin-right: 4;
    }

    #confirm_no {
        color: #f0656b;         /* coral/red, like our FAIL badges */
        width: auto;
    }
    """

    def __init__(self, message: str) -> None:
        # We save the question we want to ask so compose() can show it.
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static(self.message, id="confirm_message"),
            Horizontal(
                Static("[Y] YES", id="confirm_yes"),
                Static("[N] NO", id="confirm_no"),
                id="confirm_buttons",
            ),
            id="confirm_box",
        )

    def on_key(self, event) -> None:
        # self.dismiss(...) closes the popup and sends the answer back to
        # whoever opened it.
        if event.key == "y":
            self.dismiss(True)
        elif event.key in ("n", "escape"):
            self.dismiss(False)

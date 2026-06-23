from textual.widgets import Static
from textual.containers import Vertical
from textual.app import ComposeResult
from textual.reactive import reactive


class LoadingOverlay(Static):
    """Centered loading overlay — guaranteed visible version."""

    DEFAULT_CSS = """
    LoadingOverlay {
        width: 100%;
        height: 100%;
        align: center middle;
        layer: above;
        display: none;
    }

    LoadingOverlay.visible {
        display: block;
    }

    #loading-stack {
        width: auto;
        height: auto;
        align: center middle;
        padding: 1 4;
        border: round #00e5cc;
        background: #0a0f0f;
    }

    #loading-spinner {
        color: #00ffff;
        text-style: bold;
        height: 1;
        width: auto;
        content-align: center middle;
        text-align: center;
    }

    #loading-message {
        color: #ffffff;
        height: 1;
        width: auto;
        content-align: center middle;
        margin-top: 1;
        text-align: center;
    }
    """

    visible: reactive[bool] = reactive(False)
    _FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str = "Loading...", **kwargs):
        super().__init__(**kwargs)
        self._message = message
        self._frame = 0
        self._timer = None

    def compose(self) -> ComposeResult:
        with Vertical(id="loading-stack"):
            yield Static(self._FRAMES[0], id="loading-spinner")
            yield Static(self._message, id="loading-message")

    def show(self, message: str | None = None) -> None:
        if message:
            self._message = message
            self.query_one("#loading-message", Static).update(message)
        self.visible = True
        self.refresh()

    def hide(self) -> None:
        self.visible = False
        self.refresh()

    def on_mount(self) -> None:
        self._timer = self.set_interval(0.08, self._tick)

    def _tick(self) -> None:
        if not self.visible:
            return
        self._frame = (self._frame + 1) % len(self._FRAMES)
        self.query_one("#loading-spinner", Static).update(self._FRAMES[self._frame])

    def watch_visible(self, visible: bool) -> None:
        if visible:
            self.add_class("visible")
        else:
            self.remove_class("visible")
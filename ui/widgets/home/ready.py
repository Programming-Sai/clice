from textual.app import  ComposeResult
from textual.widgets import Static
from textual.containers import Horizontal


class ReadyPanel(Static):
    def compose(self) -> ComposeResult:
        yield Static("║ SYSTEM STATUS ║", classes="panel-title")

        with Horizontal(classes="check-row"):
            yield Static("Docker engine",       classes="check-label")
            yield Static("\[CONNECTED]",          classes="check-ok")

        with Horizontal(classes="check-row"):
            yield Static("Challenge registry",   classes="check-label")
            # yield Static("\[OUT-OF-SYNC]",           classes="check-fail")
            yield Static("\[SYNCED]",           classes="check-ok")

        with Horizontal(classes="check-row"):
            yield Static("Challenges available", classes="check-label")
            yield Static("\[124]",           classes="check-ok")
            


    def on_mount(self) -> None:
        self.border_title = "02 / READY TO START?"

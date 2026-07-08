from textual.app import  ComposeResult
from textual.widgets import Static


class AboutPanel(Static):
    def compose(self) -> ComposeResult:
        yield Static("║ WHAT IS CLICE? ║", classes="panel-title")
        yield Static(
            "CLICE evaluates your command-line competence through\n"
            "timed, scored challenges. Sessions presents a real tasks you solve and CLICE grades it."
            ,
            id="about-text"
        )

    def on_mount(self) -> None:
        self.border_title = "01 / ABOUT"

# ui/widgets/home/logo.py
from textual.widgets import Static

class LogoWidget(Static):
    DEFAULT_CSS = """
    LogoWidget {
        height: 7;
        color: #00e5cc;
        content-align: center middle;
        width: 100%;
    }
    """
    
    ASCII_LOGO = r"""
  ____  _     ___ ____ _____
 / ___|| |   |_ _/ ___| ____|
| |    | |    | | |   |  _|
| |___ | |___ | | |___| |___
 \____||_____|___\____|_____|
"""

    def render(self) -> str:
        return self.ASCII_LOGO
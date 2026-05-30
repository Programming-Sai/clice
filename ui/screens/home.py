# ui/screens/home.py
from pathlib import Path
from textual.screen import Screen
from textual.containers import Horizontal, Vertical
from textual.widgets import Static

# Import your widgets
from ..widgets.home.logo import LogoWidget
from ..widgets.home.about import AboutPanel
from ..widgets.home.ready import ReadyPanel
from ..widgets.home.activity import ActivityPanel
from ..widgets.status_bar import StatusBar

class HomeScreen(Screen):
    """Home screen with its own CSS"""
    
    # Load CSS specific to this screen
    CSS_PATH = Path(__file__).parent / "home.tcss"
    
    def compose(self):
        with Horizontal(id="header"):
            with Vertical(id="header-center"):
                yield LogoWidget(id="logo-area")
                yield Static("Command Line Interface Competence Evaluator", id="app-tagline")
        
        with Horizontal(id="main-row"):
            with Vertical(id="left-col"):
                yield AboutPanel(classes="panel")
                yield ReadyPanel(classes="panel")
            with Vertical(id="right-col"):
                yield ActivityPanel(classes="panel")
        
        yield StatusBar()
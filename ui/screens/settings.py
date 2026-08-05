
from textual.app import App, ComposeResult          # The main app "box"
from textual.containers import Vertical, Horizontal  # Boxes to stack/line-up widgets
from textual.widgets import Static, DataTable, Input  # Our LEGO bricks
from textual.screen import Screen
from textual.binding import Binding
from ui.widgets.footer import Footer


BRAND      = "#00e5cc"   # main teal  - borders, section headers, prompts
ACCENT_OK  = "#4ade80"   # bright green - "everything is fine" status text
ACCENT_ERR = "#ff4444"   # bright red   - "something's wrong" status text
DIM_BORDER = "#1e3a3a"   # dark teal    - the color of most panel borders
BG         = "#0a0a0a"   # near-black background, used across every screen
DIM_TEXT   = "#888888"   # soft grey    - secondary/label text, hints


# ---------------------------------------------------------------------
# Column widths - a design DECISION, not a measurement
# ---------------------------------------------------------------------

KEY_WIDTH = 20
CURRENT_WIDTH = 20
DEFAULT_WIDTH = 20
DESCRIPTION_WIDTH = 26

# DataTable puts a little breathing room on both sides of every
# cell automatically (1 space left, 1 space right) - that's what
# "CELL_PADDING" accounts for below.
CELL_PADDING = 1
COLUMN_WIDTHS = [KEY_WIDTH, CURRENT_WIDTH, DEFAULT_WIDTH, DESCRIPTION_WIDTH]

# Now we can CALCULATE the table's total width from those cubby
# sizes, instead of guessing or measuring it after the fact:
#   - add up all the column cubbies
#   - add each column's left+right breathing room
#   - add 4 more: 2 for #table-box's left+right border line,
#     and 2 for #table-box's own left+right padding (see APP_CSS)
TABLE_WIDTH = (
    sum(COLUMN_WIDTHS)
    + (2 * CELL_PADDING * len(COLUMN_WIDTHS))
    + 4
)


# ---------------------------------------------------------------------
# STEP 1: The look of our app (the "paint and stickers")
# ---------------------------------------------------------------------

APP_CSS = f"""


/* A wrapper that hugs the table's real width (instead of stretching
   all the way across the screen), so we can then center that whole
   little bundle on the page. */
#content-wrap {{
    width: auto;
    height: auto;
}}


#table-box {{
    border: tall {DIM_BORDER};
    margin: 1 0;
    padding: 0 1;
    width: {TABLE_WIDTH};
    height: auto;
}}

/* The settings table itself - fills 100% of #table-box's inside,
   rather than "auto"-sizing itself to its own content. */
#config-table {{
    background: {BG};
    color: {DIM_TEXT};
    width: 100%;
    height: auto;
}}


DataTable > .datatable--header {{
    color: {DIM_TEXT};
    text-style: bold;
    background: {BG};
}}

DataTable > .datatable--cursor {{
    background: {BRAND};
    color: {BG};
}}


#command-box {{
    border: tall {DIM_BORDER};
    background: {BG};
    margin: 0 0 1 0;
    height: 3;
    align: left middle;
    /* Matches #table-box's width on purpose - see the TABLE_WIDTH
       comment near the top of this file for why. */
    width: {TABLE_WIDTH};
}}


#prompt-symbol {{
    color: {BRAND};
    text-style: bold;
    width: auto;
    padding: 0 0 0 1;
}}

/* The actual text input where the user types */
#command-input {{
    background: {BG};
    border: none;
    color: {BRAND};
}}
#command-input:focus {{
    border: none;
}}



/* Push everything above the footer to the top of the screen, and
   center our little "content-wrap" bundle left-to-right. */
#body {{
    height: 1fr;
    align: center top;
}}
"""


class SettingsScreen(Screen):
    """
    This is our whole app! Every Textual app is a Python "class"
    that inherits from App - think of App as a pre-built empty
    toy box, and we're the ones filling it with our own toys.
    """

    # Attach the CSS "paint" we wrote above to this app.
    CSS = APP_CSS

    settings={
        "resources":{
            "memory":{
                "current":"512m",
                "default":"1g",
                "description":"Max memory allocation",
            },
            "cpu_cores":{
                "current":"1.0",
                "default":"1.0",
                "description": "CPU cores allocated",
            },
            "timeout":{
                "current":"20s",
                "default":"30s",
                "description": "Checker timeout limit",
            }
        },
        "behaviour":{
            "network":{
                "current":"ENABLED",
                "default":"DISABLED",
                "description":"Allow network access",
            },
            "auto_clean":{
                "current":"ENABLED",
                "default":"ENABLED",
                "description":"Auto-cleanup containers",
            }
        },
        "ai":{
            "model":{
                "current":"nvidia/nemotron-3-ultra-550b-a55b:free",
                "default":"nvidia/nemotron-3-ultra-550b-a55b:free",
                "description":"Ai model for feedback"
            },
            "api_key":{
                "current":"sk-or-v1-***",
                "default":"...",
                "description":"Api key for Ai feedback"
            }
        }
    }

    # This is the pretend data for our settings table - a list of
    # rows, and each row is a small list of 4 pieces of info:
    # [ KEY, CURRENT VALUE, DEFAULT VALUE, DESCRIPTION ]
    # In a real app you might load this from a file or a program,
    # but for our starting point we just type it in by hand.

    ROWS = []
    for k, v in settings.items():
        for sk, sv in v.items():
            ROWS.append((k+"."+sk, sv["current"], sv["default"], sv["description"]))

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", show=True),
    ]

    def compose(self) -> ComposeResult:
        """
        `compose` is where we say "here are all my LEGO bricks and
        here is the order I want to snap them together in."
        Textual calls this automatically when the app starts.
        `yield` just means "add this brick to the screen now."
        """

        # A Vertical box stacks its children top-to-bottom, like
        # stacking pancakes. Because #body has "align: center top"
        # in the CSS, whatever we put inside it will sit in the
        # middle of the screen sideways.
        with Vertical(id="body"):


            # "content-wrap" is a small bundle that only takes up as
            # much room as its widest child (the table) needs -
            # that's what lets the whole group shrink-to-fit AND
            # get centered together as one unit.
            with Vertical(id="content-wrap"):

                # 2) A bordered box containing our settings table.
                with Vertical(id="table-box"):
                    yield DataTable(id="config-table", cursor_type="cell")

                # 3) The command input box, styled like "/ > type here".
                #    We put the "/" symbol and the actual Input side
                #    by side using a Horizontal box (left-to-right).
                with Horizontal(id="command-box"):
                    yield Static(">", id="prompt-symbol")
                    yield Input(
                        placeholder="set resource.memory 1024",
                        id="command-input",
                    )


        yield Footer()


    def on_mount(self) -> None:
        """
        `on_mount` runs one time, right after the app has finished
        building itself - like the moment right after you finish
        building a LEGO set and it's ready to play with.

        We use it here to fill in our DataTable with columns and
        rows, and to move the little cursor highlight onto the
        "512 MB" cell, just like the picture shows.
        """

        # Grab the table LEGO brick by the id we gave it, so we can
        # tell it what to show.
        self.query_one(Footer).set_screen("settings")
        table = self.query_one("#config-table", DataTable)

        table.add_column("KEY", width=KEY_WIDTH)
        table.add_column("CURRENT", width=CURRENT_WIDTH)
        table.add_column("DEFAULT", width=DEFAULT_WIDTH)
        table.add_column("DESCRIPTION", width=DESCRIPTION_WIDTH)


        for row in self.ROWS:
            table.add_row(*row, height=None)

        # Turn off the little numbered "row label" column on the far
        # left that Textual shows by default - the picture doesn't
        # have one.
        table.show_row_labels = False

        # Move the highlighted cell to row 0 ("resource.memory"),
        # column 1 (the "CURRENT" column) - this matches the cyan
        # highlighted "512 MB" box in the picture.
        table.cursor_coordinate = (0, 1)

        # Put the typing cursor straight into the command input box,
        # so the user can start typing immediately, no clicking
        # needed.
        self.query_one("#command-input", Input).focus()

    def get_css_variables(self) -> dict[str, str]:
        """
        Textual calls this before it reads our CSS, to ask "hey, do
        you have any custom $variables I should know about?" We hand
        back our TABLE_WIDTH number here, turning it into the
        "$table-width" variable used up in APP_CSS.
        """
        variables = super().get_css_variables()
        variables["table-width"] = str(TABLE_WIDTH)
        return variables



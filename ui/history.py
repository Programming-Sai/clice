"""
CLICE - SESSION HISTORY
========================

Hi! This is a "Textual" app. Textual is a Python toy box that lets us build
apps that live inside the terminal (the black window with text), but they
can look almost like a real website! Things can have colors, boxes, and
you can click on them or press keys, just like a video game menu.

Here is the big idea, in kid words:
  - We build little LEGO blocks called "widgets" (a table, a search box,
    some text).
  - We stick the LEGO blocks together in a "layout" (who goes where).
  - We paint them using CSS rules (color instructions) written right here
    in this same file, inside DEFAULT_CSS.
  - We tell Textual what to do when someone types something.

WHAT CHANGED THIS ROUND (so you can see the "why"):
  1. FOUND THE MISSING-FOOTER BUG! The bottom bar was set to a fixed
     height: 1, but then we gave it a border-top line too - which needs
     its OWN line of space. Textual reserved room for the docked bottom
     bar based on the height we declared (1), not the extra line the
     border added, so the border rendered but the actual footer TEXT got
     pushed one line past the bottom of the screen and disappeared.
     Fixed by changing height: 1 to height: auto (with min-height: 1) so
     Textual measures the real size - border included - before reserving
     its spot at the bottom.
  2. The top bar is commented out for now (removed on purpose) - the
     rest of the layout doesn't depend on it, so everything below just
     shifts up to fill the space.

WHAT CHANGED THIS ROUND (so you can see the "why"):
  1. Added an EMPTY STATE. Before, if you cleared all the sessions (or
     searched for something that matched nothing), the table area just
     went blank - which looks like something broke! Now a friendly
     message takes the table's place instead, and the message itself
     changes depending on WHY it's empty: "no sessions yet" after a
     clear-all, or "no sessions match ..." when a search comes up empty.

Let's go!
"""

# We need to "import" (borrow) some tools from the textual toy box.
from textual.app import App, ComposeResult          # App = the whole program. ComposeResult = the list of widgets we build.
from textual.containers import Horizontal, Vertical  # Boxes that line widgets up in a row, or stack them up.
from textual.widgets import Static, DataTable, Input  # Static = plain text. DataTable = a spreadsheet-like grid.
from textual.screen import ModalScreen                # ModalScreen = a little popup window that floats on top.
from textual.binding import Binding                   # Binding = "when this key is pressed, run this action."


# ---------------------------------------------------------------------------
# STEP 1: OUR PRETEND DATA
# ---------------------------------------------------------------------------
# In a real app this list might come from a file or the internet. For our
# base/starter project, we just type it in by hand, just like the picture
# you showed me. Each session is one row in our table.
#
# Each row is a Python "tuple" (a tiny bundle of values) in this order:
#   (number, timestamp, challenge name, duration, number of commands, status)
SESSION_DATA = [
    ("012", "2023.10.24 14:12", "GREP-BASICS",    "03:12", "14", "PASS"),
    ("011", "2023.10.24 13:55", "HELLO-CLICE",    "00:45", "03", "PASS"),
    ("010", "2023.10.24 13:01", "TAR-ARCHIVE",    "01:45", "08", "FAIL"),
    ("009", "2023.10.24 12:45", "CRON-JOBS-V1",   "00:52", "05", "PASS"),
    ("008", "2023.10.24 12:20", "SUDO-LINT",      "00:12", "02", "PASS"),
    ("007", "2023.10.24 11:58", "SSH-KEYGEN-WK",  "04:30", "19", "PASS"),
    ("006", "2023.10.24 11:34", "AWK-FILTER",     "02:05", "09", "PASS"),
    ("005", "2023.10.24 11:10", "CHMOD-DRILL",    "01:10", "04", "FAIL"),
    ("004", "2023.10.24 10:52", "FIND-EXEC",      "03:44", "15", "PASS"),
    ("003", "2023.10.24 10:30", "CURL-HEADERS",   "00:38", "03", "PASS"),
    ("002", "2023.10.24 10:05", "PIPE-CHAIN",     "02:21", "11", "PASS"),
    ("001", "2023.10.24 09:48", "ENV-VARS-V2",    "01:55", "06", "FAIL"),
]


# ---------------------------------------------------------------------------
# STEP 2: THE TOP BAR  (the row that says "CLICE | SESSION HISTORY ... RESULTS")
# ---------------------------------------------------------------------------
class TopBar(Horizontal):
    """
    A widget is just a Python "class" (a cookie-cutter shape) that describes
    one piece of our screen. This one is the very top bar of the app.

    "Horizontal" means the things inside line up in a row, left to right,
    like books on a shelf.
    """

    def compose(self) -> ComposeResult:
        # "yield" means "add this widget to the screen, one at a time."
        # id="..." gives each widget a name tag so our CSS can find it and
        # color it correctly later.
        yield Static("CLICE", id="brand")
        yield Static("SESSION HISTORY", id="brand_sub")
        # This empty stretchy box pushes the nav items to the right side,
        # kind of like a spring in the middle of the shelf.
        yield Static("", classes="spacer")
        yield Static("SYSTEM", classes="nav_item")
        yield Static("CHALLENGES", classes="nav_item")
        yield Static("SESSION", classes="nav_item")
        yield Static("RESULTS", classes="nav_item nav_active")  # this tab is "on"


# ---------------------------------------------------------------------------
# STEP 3: THE STATS BAR  (TOTAL SESSIONS / SUCCESS RATE / AVG. TIME)
# ---------------------------------------------------------------------------
class StatsBar(Horizontal):
    """
    Shows the little summary numbers near the top, like a scoreboard.

    KID-FRIENDLY BUG STORY: the very first version of this put the label
    ("TOTAL SESSIONS") and the value ("12 SESSIONS") in two separate little
    Static widgets, stacked inside a "Vertical" box set to width: auto.
    That's what made them vanish on wide screens! When a box says
    "auto", Textual has to measure its children to know how wide to make
    it - and stacking two auto-width things inside another auto-width box
    sometimes confuses that measurement, so the box shrank to nothing.

    THE FIX: each stat below is now just ONE Static widget with the label
    and value written on two lines inside a single string (using "\\n" to
    make a new line), and we give it a fixed, explicit width. One widget,
    one clear size - nothing left for Textual to get confused about.
    """

    def compose(self) -> ComposeResult:
        # [dim] and [bold ...] here are Rich "markup" - little bracket tags
        # that color and style pieces of text, kind of like tiny paint
        # instructions mixed right into the words.
        #
        # This one gets an id="stat_total" because its number needs to
        # change later, whenever a session gets deleted or everything
        # gets cleared - see update_stats() further down.
        yield Static(
            "[dim]TOTAL SESSIONS[/dim]\n[bold]12 SESSIONS[/bold]",
            id="stat_total",
            classes="stat_block",
        )
        yield Static(
            "[dim]SUCCESS RATE[/dim]\n[bold #4ade80]75% PASS[/bold #4ade80]",
            classes="stat_block",
        )
        yield Static(
            "[dim]AVG. TIME[/dim]\n[bold #e0b038]00:04:12 AVG[/bold #e0b038]",
            classes="stat_block",
        )



# ---------------------------------------------------------------------------
# STEP 4: THE SEARCH ROW
# ---------------------------------------------------------------------------
# This used to also hold [ ALL ] [ PASS ] [ FAIL ] buttons. We removed them!
# Now this row is just a label and a text box. Typing in the box is the
# ONLY way to filter the table - nice and simple, all "manual."
class SearchBar(Horizontal):
    """The single search row that filters the whole table as you type."""

    def compose(self) -> ComposeResult:
        yield Static("/ Search:", id="search_label")
        # An Input is a box you can type into, like the search bar in the picture.
        # Try typing "pass", "fail", "grep", or a timestamp piece like "10.24"!
        yield Input(placeholder="type to filter... e.g. pass, fail, grep", id="search_box")


# ---------------------------------------------------------------------------
# STEP 5: THE BOTTOM BAR  (key hints + storage size)
# ---------------------------------------------------------------------------
class BottomBar(Horizontal):
    """The footer strip at the very bottom of the screen."""

    def compose(self) -> ComposeResult:
        yield Static("[ENTER] VIEW DETAILS", classes="hint")
        yield Static("[D] DELETE", classes="hint")
        yield Static("[C] CLEAR ALL", classes="hint")
        yield Static("[ESC] BACK", classes="hint")
        yield Static("", classes="spacer")
        yield Static("12.4GB / 32GB", id="storage")
        yield Static("STABLE", id="stable_tag")


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


# ---------------------------------------------------------------------------
# STEP 6: THE WHOLE APP  (this glues every piece together)
# ---------------------------------------------------------------------------
class ClicedApp(App):
    """
    This is the main "App" class. Every Textual program needs exactly one
    of these. It's like the box that all our LEGO pieces live inside.
    """

    # We turn OFF Textual's "use my terminal's own color scheme" behavior.
    # Without this, some terminals will swap our exact colors for their
    # own approximate versions (this is actually why colors looked wrong
    # and pink/purple before - the terminal was repainting them!). Setting
    # this to False says "always use the EXACT colors we picked, no matter
    # whose terminal this runs in."
    ansi_color = False

    # BINDINGS is Textual's list of "when this key is pressed, run this
    # action" rules. show=False just means "don't add this to Textual's
    # own automatic footer" - we're drawing our own footer by hand with
    # BottomBar, so we don't need Textual's built-in one too.
    #
    # HEADS UP: these only fire when the DataTable has focus, not while
    # you're typing in the search box - otherwise pressing "d" while
    # searching would delete something instead of typing the letter d!
    # Press Tab (or click a row) to move focus to the table first.
    BINDINGS = [
        Binding("d", "delete_row", "Delete", show=False),
        Binding("c", "clear_all", "Clear All", show=False),
    ]

    # This big triple-quoted string is our CSS - a list of coloring rules.
    # It's like a coloring book instructions sheet. It doesn't run any
    # logic (no clicking, no thinking) - it just says "make this thing
    # THIS color" or "make this box THIS wide."
    #
    # A rule looks like this:
    #
    #     #some_id {
    #         color: cyan;
    #     }
    #
    # The "#some_id" part means "find the widget with id='some_id'".
    # A rule that starts with a dot, like ".some_class", means "find every
    # widget that has classes='some_class'" (there can be many!).
    #
    # EVERY box below uses the SAME background color variable-like value:
    # #131313. That's the exact dark grey/black we sampled from your
    # screenshot. Using one single value everywhere is what makes the
    # background look "uniform" instead of patchy.
    DEFAULT_CSS = """
    /* The whole screen's background and default text color. */
    Screen {
        background: #131313;
        color: #c8d3d9;
    }

    /* -------------------------------------------------------------
       TOP BAR
    ------------------------------------------------------------- */
    #top_bar {
        height: auto;            /* grow to fit its contents - never clips! */
        min-height: 3;
        background: #131313;     /* same background as everything else */
        border-bottom: solid #005f5f;   /* teal border, sampled from your new screenshot */
        padding: 1 2;             /* a little breathing room inside */
        align: left middle;       /* line everything up in the middle vertically */
    }

    #brand {
        color: #00fbfa;           /* bright cyan, sampled from your logo text */
        text-style: bold;
        width: auto;
    }

    #brand_sub {
        color: #7d8b96;
        width: auto;
        margin-left: 2;
    }

    /* This invisible box grows to fill empty space, pushing things apart -
       like an invisible spring between books on a shelf. */
    .spacer {
        width: 1fr;
        background: #131313;
    }

    .nav_item {
        width: auto;
        color: #7d8b96;
        margin-left: 3;
    }

    /* The currently selected nav tab (RESULTS) glows cyan with an underline. */
    .nav_active {
        color: #00fbfa;
        text-style: bold underline;
    }

    /* -------------------------------------------------------------
       STATS BAR
    ------------------------------------------------------------- */
    #stats_bar {
        height: auto;             /* grow to fit its contents - never clips! */
        min-height: 4;
        background: #131313;
        border-bottom: solid #005f5f;   /* same teal border as the top bar */
        padding: 1 2;
        align: left middle;
    }

    /* Each stat block gets a FIXED width instead of "auto". A fixed
       number (like 28) never needs Textual to "measure" anything, so it
       can never collapse to zero - that's the whole bug fix. */
    .stat_block {
        width: 28;
        height: auto;
        background: #131313;
    }

    /* -------------------------------------------------------------
       SEARCH BAR
    ------------------------------------------------------------- */
    #search_bar {
        height: 1;                 /* exactly one line tall - no extra blank space below */
        background: #131313;
        align: left middle;
        padding: 0 2;
    }

    #search_label {
        width: auto;
        color: #c8d3d9;
        background: #131313;
        text-style: bold;
    }

    #search_box {
        width: 1fr;                 /* 1fr = "stretch and fill whatever room is left" */
        height: 1;                  /* one line tall, matches the row around it */
        margin-left: 1;
        background: #1a1a1a;        /* just a touch lighter so you can see the box */
        color: #00fbfa;
        border: none;
        padding: 0;                 /* no extra space above/below the typed text */
    }

    /* -------------------------------------------------------------
       THE MAIN TABLE
    ------------------------------------------------------------- */
    /* This is the big change inspired by your new screenshot: a full
       teal border box around the table, just like the CHALLENGE_DETAILS
       panel in that design. height: 1fr makes this box stretch to fill
       ALL the space left over between the search bar and the bottom bar
       - and because that space is limited, the DataTable inside starts
       scrolling ITSELF instead of the whole screen scrolling. That's
       what keeps the top bar, stats bar, and search bar frozen in place
       while only the table content moves. */
    #table_panel {
        border: solid #005f5f;     /* the teal border box, sampled from your screenshot */
        height: 1fr;
        background: #131313;
        padding: 0 0 1 0;           /* one blank line of breathing room at the very bottom */
    }

    #session_table {
        background: #131313;
        color: #c8d3d9;
        width: 1fr;
        height: 1fr;                /* fill the whole panel so IT scrolls, not the screen */
    }

    /* -------------------------------------------------------------
       EMPTY STATE
    ------------------------------------------------------------- */
    /* This is what shows up INSTEAD of the table whenever there are no
       rows to display - either because every session got deleted, or
       because the search box doesn't match anything. It starts hidden
       (display: none) and refresh_table() below flips it on/off. */
    #empty_state {
        display: none;
        width: 1fr;
        height: 1fr;
        content-align: center middle;   /* centers the text both ways */
        color: #5c6b76;
        text-align: center;
    }

    /* This class is what actually does the showing/hiding - Textual lets
       us just add or remove a class instead of writing an if/else for
       every single style property. */
    #empty_state.visible {
        display: block;
    }

    /* The header row of the table (#, TIMESTAMP, CHALLENGE, ...) */
    #session_table > .datatable--header {
        background: #131313;
        color: #7d8b96;
        text-style: bold;
    }

    /* The row your cursor/keyboard is currently sitting on - bright cyan,
       just like the highlighted row in your picture! */
    #session_table > .datatable--cursor {
        background: #00fbfa;
        color: #131313;
    }

    /* -------------------------------------------------------------
       BOTTOM BAR
    ------------------------------------------------------------- */
    #bottom_bar {
        height: auto;               /* let it size itself, border included - see note below */
        min-height: 1;
        background: #131313;
        dock: bottom;              /* glue this bar to the very bottom of the screen */
        border-top: solid #005f5f;  /* same teal separator style as the rest of the app */
        padding: 0 2;
        align: left middle;
    }

    .hint {
        width: auto;
        color: #5c6b76;
        background: #131313;
        margin-right: 3;
    }

    #storage {
        width: auto;
        color: #5c6b76;
        background: #131313;
        margin-right: 2;
    }

    #stable_tag {
        width: auto;
        color: #4ade80;
        background: #131313;
    }
    """

    def compose(self) -> ComposeResult:
        """
        This function runs once, when the app starts. It says exactly which
        big pieces go on the screen, from top to bottom.
        """
        # The top bar is commented out for now (removed on purpose) - the
        # app still works fine without it, everything below just shifts up.
        # yield TopBar(id="top_bar")
        yield StatsBar(id="stats_bar")
        yield SearchBar(id="search_bar")
        # The table now lives inside a bordered "panel" box (id="table_panel").
        # This box is the thing that stretches to fill the leftover space
        # and scrolls - everything else above and below it stays put.
        #
        # We also tuck an "empty state" message in here right alongside
        # the table. Only ONE of the two is ever visible at a time -
        # refresh_table() decides which, based on whether there's
        # anything to show.
        yield Vertical(
            DataTable(id="session_table"),
            Static(
                "( no sessions found )\ntry clearing your search, or nothing's here to show",
                id="empty_state",
            ),
            id="table_panel",
        )
        yield BottomBar(id="bottom_bar")

    def on_mount(self) -> None:
        """
        "on_mount" runs automatically right after the app appears on screen.
        This is where we set up our DataTable: give it column headers and
        fill it with our pretend data.
        """
        # SESSION_DATA up top is our ORIGINAL template - we never want to
        # change that one directly. Instead we make a live COPY here
        # (list(...) makes a fresh new list with the same items) that we
        # ARE allowed to delete things from. self.session_data is what
        # delete/clear-all actually change from now on.
        self.session_data = list(SESSION_DATA)

        table = self.query_one("#session_table", DataTable)

        # cursor_type "row" means when you press up/down, a whole row lights
        # up (just like the highlighted cyan row in your picture).
        table.cursor_type = "row"
        table.zebra_stripes = False  # no alternating stripes, matches the flat look in the image

        # cell_padding adds extra empty space BETWEEN columns, so the text
        # doesn't feel cramped and the table "fills out the width" nicely.
        table.cell_padding = 3

        # header_height=3 makes the header row 3 lines tall, and we wrap
        # each column name in "\n" below - the exact same padding trick
        # we use for every data row, so the header now matches them.
        table.header_height = 3

        # We add each column one at a time (instead of add_columns) so we
        # can give TIMESTAMP and CHALLENGE extra "width" - this is what
        # spreads the columns out to fill the wider table nicely.
        table.add_column("\n#\n", width=8)
        table.add_column("\nTIMESTAMP\n", width=24)
        table.add_column("\nCHALLENGE\n", width=28)
        table.add_column("\nDURATION\n", width=16)
        table.add_column("\nCMDS\n", width=12)
        table.add_column("\nSTATUS\n", width=18)

        # Now we fill the table using our filtering helper (explained below).
        self.refresh_table()

    def refresh_table(self) -> None:
        """
        This function decides WHICH rows to show, based on whatever text is
        typed in the search box. There are no more tab buttons - typing is
        the only way to filter now, which is what makes this "manual."

        Every time the search text changes (or a row gets deleted), we call
        this again to redraw the table with the right rows.
        """
        table = self.query_one("#session_table", DataTable)
        table.clear()  # wipe the table clean before we add the new rows

        search_box = self.query_one("#search_box", Input)
        # .lower() makes searching work no matter if you type big or small letters
        search_text = search_box.value.lower()

        for row in self.session_data:
            number, timestamp, challenge, duration, cmds, status = row

            # We build one big lowercase string out of EVERY column in this
            # row, so typing "pass", "fail", "grep", or even part of the
            # timestamp will all correctly match. This is how "all the
            # filtering" now happens manually, from one single search box.
            haystack = " ".join(
                [number, timestamp, challenge, duration, cmds, status]
            ).lower()

            if search_text and search_text not in haystack:
                continue  # "continue" means "skip this row, go to the next one"

            # If we got past that check, this row is allowed to show!
            # We color PASS green and FAIL red/coral using EXACT hex colors
            # (not color names like "red"), so the colors always look the
            # same no matter what terminal this runs in.
            if status == "PASS":
                status_text = "[#4ade80][PASS] \u2713[/#4ade80]"
            else:
                status_text = "[#f0656b][FAIL] \u2717[/#f0656b]"

            # THE PADDING TRICK: wrapping each cell's text in "\n" (a blank
            # line) before and after adds one empty line above and below
            # every row. We also tell add_row height=3 so there's room for
            # those blank lines to actually show up.
            #
            # key=number tags this row with its session number "behind the
            # scenes" - that's how action_delete_row (below) knows exactly
            # WHICH session to remove when you press D on a highlighted row.
            table.add_row(
                f"\n{number}\n",
                f"\n{timestamp}\n",
                f"\n{challenge}\n",
                f"\n{duration}\n",
                f"\n{cmds}\n",
                f"\n{status_text}\n",
                height=3,
                key=number,
            )

        # THE EMPTY STATE: after the loop above, if the table still has
        # zero rows, we hide the table and show a friendly message
        # instead of just... nothing. We pick a different message
        # depending on WHY it's empty, so it actually tells you what to
        # do next instead of just looking broken.
        empty_state = self.query_one("#empty_state", Static)
        if table.row_count == 0:
            if not self.session_data:
                # every session was deleted/cleared - there's genuinely
                # nothing left at all.
                empty_state.update("( no sessions yet )\npress D on a row to delete one, or C to clear all")
            else:
                # sessions exist, but none of them match what's typed
                # into the search box.
                empty_state.update(f"( no sessions match \"{search_box.value}\" )\ntry a different search, or clear the search box")
            empty_state.add_class("visible")
            table.display = False
        else:
            empty_state.remove_class("visible")
            table.display = True

    def update_stats(self) -> None:
        """
        Updates the "TOTAL SESSIONS" number after a delete or clear-all, so
        the stats bar always matches what's really in the table. (SUCCESS
        RATE and AVG. TIME stay fixed for now to keep this starter project
        simple - recalculating those from self.session_data would be a fun
        next step to try yourself!)
        """
        total = len(self.session_data)
        stat_total = self.query_one("#stat_total", Static)
        stat_total.update(f"[dim]TOTAL SESSIONS[/dim]\n[bold]{total} SESSIONS[/bold]")

    # -----------------------------------------------------------------
    # STEP 7: REACTING TO TYPING
    # -----------------------------------------------------------------
    def on_input_changed(self, event: Input.Changed) -> None:
        """
        This runs automatically every time the text inside our search Input
        changes (every single letter you type triggers this!).
        """
        if event.input.id == "search_box":
            self.refresh_table()

    # -----------------------------------------------------------------
    # STEP 8: DELETE ONE ROW  (press D on a highlighted row)
    # -----------------------------------------------------------------
    def action_delete_row(self) -> None:
        """
        This runs when you press "d" while the table has focus. It never
        deletes anything right away - it always asks first, using our
        ConfirmModal popup, since deleting is something you can't undo.
        """
        table = self.query_one("#session_table", DataTable)

        # If the table is empty, or nothing is highlighted, there's
        # nothing to delete - just do nothing instead of crashing.
        if table.row_count == 0:
            return

        # table.cursor_row is the highlighted row's POSITION (like "3rd
        # row"). We use coordinate_to_cell_key to turn that position into
        # the actual "key" we tagged the row with back in refresh_table
        # (remember key=number) - that key is what tells us WHICH session
        # this really is, no matter how the table has been sorted/filtered.
        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        session_number = row_key.value

        # Find the matching challenge name just so our question is
        # friendlier than "delete session #005?" - e.g. "delete
        # CHMOD-DRILL?"
        challenge_name = next(
            (row[2] for row in self.session_data if row[0] == session_number),
            session_number,
        )

        def handle_answer(confirmed: bool | None) -> None:
            # confirmed is True (pressed Y), False (pressed N/Escape), or
            # None if the popup got closed some other way - only act on True.
            if confirmed:
                self.session_data = [
                    row for row in self.session_data if row[0] != session_number
                ]
                self.refresh_table()
                self.update_stats()

        # push_screen shows our popup ON TOP of the app, and runs
        # handle_answer with whatever the popup dismiss()-es with.
        self.push_screen(
            ConfirmModal(f"Delete session {challenge_name}? This can't be undone."),
            handle_answer,
        )

    # -----------------------------------------------------------------
    # STEP 9: CLEAR EVERYTHING  (press C anywhere the table has focus)
    # -----------------------------------------------------------------
    def action_clear_all(self) -> None:
        """
        This runs when you press "c" while the table has focus. Just like
        delete, it asks for confirmation first - clearing EVERYTHING is
        extra risky, so we don't want one accidental key press to wipe
        out the whole table.
        """
        if not self.session_data:
            return  # already empty - nothing to clear

        def handle_answer(confirmed: bool | None) -> None:
            if confirmed:
                self.session_data = []
                self.refresh_table()
                self.update_stats()

        self.push_screen(
            ConfirmModal("Clear ALL sessions? This can't be undone."),
            handle_answer,
        )


# ---------------------------------------------------------------------------
# STEP 8: ACTUALLY START THE APP
# ---------------------------------------------------------------------------
# Python runs this bottom part only when you run this file directly
# (not when some other file imports it). It's like the "GO" button.
if __name__ == "__main__":
    app = ClicedApp()
    app.run()
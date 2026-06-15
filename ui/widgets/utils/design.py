


IS_PASSING: bool = False   # ← change to True to see the FAIL screen


# ══════════════════════════════════════════════════════════════════════════════
#  🎨 COLOUR PALETTE
# ══════════════════════════════════════════════════════════════════════════════
#
# Giving colours friendly names means we only change a hex code in ONE place
# and it updates everywhere on the screen automatically.

BRAND      = "#00e5cc"   # main teal  — borders, section headers, timestamps
ACCENT_OK  = "#00ff88"   # bright green — scores, exit codes on PASS
ACCENT_ERR = "#ff3c3c"   # bright red   — scores, exit codes on FAIL
DIM_BRAND  = "#005c54"   # dark teal    — muted separators, dim borders
BG         = "#0a0f0e"   # near-black background
TEXT       = "#c8fff9"   # soft off-white — main readable body text
DIM_TEXT   = "#4a8f88"   # dim teal-grey  — labels, secondary info

# Pick the live accent based on the master switch.
# Python ternary syntax:  value_if_true  if  condition  else  value_if_false
ACCENT = ACCENT_OK if IS_PASSING else ACCENT_ERR

def get_difficulty_color(difficulty):
    if difficulty == "beginner":
        return '#00ff88'
    elif difficulty == "intermediate":
        return '#ff9900'
    elif difficulty == "advanced":
        return '#ff3333'

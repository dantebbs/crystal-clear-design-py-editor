
# A default name for convenience.
HSM_DEFAULT_FILENAME = "hsm_model.json"

# These Reserved Words are the dictionary keys used throughout the model to access sub-fields.
RSVD_STATES = "states"
RSVD_LYOUT = "layout"
RSVD_START = "start"
RSVD_FINAL = "final"
RSVD_AUTO  = "auto"
RSVD_TRAN  = "tran"
RSVD_SRC   = "src"
RSVD_DEST  = "dest"
RSVD_PATH  = "path"
RSVD_LFT   = "x"
RSVD_TOP   = "y"
RSVD_WID   = "w"
RSVD_HGT   = "h"


# Note: This value must be even and > 0.
# Lines are routed on multiples of GRID_PIX / 2, and the corners of states are
# constrained to multiples of GRID_PIX.
GRID_PIX = 10

# A feature of multiple border weights might be added later.
# Use even numbers for all sizes to avoid misalignments in the GUI layout.
THN_LINE_SIZE = 2
THN_CRNR_SIZE = 10
THN_TITL_SIZE = 16
MED_LINE_SIZE = 4
MED_CRNR_SIZE = 12
MED_TITL_SIZE = 18
THK_LINE_SIZE = 8
THK_CRNR_SIZE = 14
THK_TITL_SIZE = 20

BRD_WEIGHT_THN_SIZES = { "line": THN_LINE_SIZE, "crnr": THN_CRNR_SIZE, "titl": THN_TITL_SIZE }
BRD_WEIGHT_MED_SIZES = { "line": MED_LINE_SIZE, "crnr": MED_CRNR_SIZE, "titl": MED_TITL_SIZE }
BRD_WEIGHT_THK_SIZES = { "line": THK_LINE_SIZE, "crnr": THK_CRNR_SIZE, "titl": THK_TITL_SIZE }
BRD_WEIGHTS = ( BRD_WEIGHT_THN_SIZES, BRD_WEIGHT_MED_SIZES, BRD_WEIGHT_THK_SIZES )

SM_OUTLINE_MIN = { RSVD_WID: 60, RSVD_HGT: 50 }

# TODO: Remove the use of default position.
# (Regular) State Machine Default Layout
SM_OUTLINE_DEF = { RSVD_LFT: 200, RSVD_TOP: 100, RSVD_WID: 120, RSVD_HGT: 90 }
# Start and Stop States are treated separately.
SS_OUTLINE_DEF = { RSVD_LFT: 100, RSVD_TOP: 60, RSVD_WID: GRID_PIX * 2, RSVD_HGT: GRID_PIX * 2 }

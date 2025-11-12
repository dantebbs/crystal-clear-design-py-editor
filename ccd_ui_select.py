import json
import os
import sys
# Note: Tkinter is usually auto-installed with python, but if you get "ImportError: No module named Tkinter":
# python -m pip install python3-tk
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import *
import workspace_settings
#import hierarchical_state_machine
import ccd_ui_hsm
import hsm_defaults

try:
    import hierarchical_state_machine as hsm
except ImportError:
    print( f"Unable to import module \"hierarchical_state_machine\"." )
    print( f"Run:\npython -m pip install hierarchical_state_machine\n    ... then try again." )
    quit()


this_module = sys.modules[__name__]
selector = None


class ccd_ui_select:
    def __init__( self, working_frame: tk.Frame, working_model: dict ):
        self.frame = working_frame
        self.model = working_model
        self.frame.canvas.bind( sequence = "<Button-1>", func = self.unresolved_click_cb )
        self.frame.canvas.bind( sequence = "<B1-Motion>", func = self.unresolved_drag_cb )
        self.frame.canvas.bind( sequence = "<ButtonRelease-1>", func = self.unresolved_stop_cb )

        #work_area_width = self.frame.winfo_width()

    def unresolved_click_cb( self, event ):
        #print( f"Click @ {event.x},{event.y}" )
        # Go through each transition path segment, and find the closest one.
        nearest = 10000000
        point = ( event.x, event.y )
        trans_list = self.frame.get_trans_list()
        #print( f"Click -> {trans_list}" )
        for transition in trans_list:
            path = transition.get( hsm_defaults.RSVD_PATH )
            for point_idx in range( len( path ) - 1 ):
                src_pt = path[ point_idx + 0 ]
                dst_pt = path[ point_idx + 1 ]
                #print( f"{point} -> {src_pt},{dst_pt}" )

    def unresolved_drag_cb( self, event ):
        #print( f"Drag -> {event}" )
        pass

    def unresolved_stop_cb( self, event ):
        #print( f"Stop -> {event}" )
        pass


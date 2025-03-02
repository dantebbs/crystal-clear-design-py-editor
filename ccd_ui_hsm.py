import json
import sys
# Note: Tkinter is usually auto-installed with python, but if you get "ImportError: No module named Tkinter":
# python -m pip install python3-tk
import tkinter as tk
from tkinter import ttk
from tkinter import *
#from tkinter.messagebox import showinfo
from PIL import Image, ImageTk
import util

import workspace_settings
import hierarchical_state_machine

try:
    import hierarchical_state_machine as hsm
except ImportError:
    print( f"Unable to import module \"hierarchical_state_machine\"." )
    print( f"Run:\npython -m pip install hierarchical_state_machine\n    ... then try again." )
    quit()



BRD_WEIGHT_THN = 0
BRD_WEIGHT_MED = 1
BRD_WEIGHT_THK = 2

# Use even numbers for these sizes to avoid misalignments.
THN_LINE_SIZE = 2
THN_CRNR_SIZE = 10
THN_TITL_SIZE = 16

MED_LINE_SIZE = 4
MED_CRNR_SIZE = 12
MED_TITL_SIZE = 18

THK_LINE_SIZE = 8
THK_CRNR_SIZE = 14
THK_TITL_SIZE = 20

MIN_SM_WID = 60
MIN_SM_HGT = 50

DEF_STATE_LFT = 200
DEF_STATE_TOP = 100
DEF_STATE_WID = 120
DEF_STATE_HGT = 90

# Reserved Words
HSM_RSVD_LYOUT = "layout"
HSM_RSVD_START = "start"
HSM_RSVD_FINAL = "final"
HSM_RSVD_AUTO  = "auto"
HSM_RSVD_TRAN  = "tran"
HSM_RSVD_PATH  = "path"

# Note: This value must be even and > 0.
# Lines are routed on multiples of GRID_PIX / 2, and the corners of states are
# constrained to multiples of GRID_PIX.
GRID_PIX = 10

# Get the name of this particular code module.
this_module = sys.modules[__name__]

# A flag showing that one or more changes has been made, and the model needs
# to be saved to file again.
have_changes = False


# The State Layout Widget
class sm_start_final_state_layout( tk.Canvas ):
    def __init__( self, state_name, model, x, y, *args, **kwargs ):
        self.initialized = False
        assert( state_name == HSM_RSVD_START or state_name == HSM_RSVD_FINAL )
        self.name = state_name
        self.model = model
        #print( f"start/final model={self.model}." )
        # Set border, which for the start symbol, also sets the width and height.
        self.set_border_thickness( BRD_WEIGHT_THN )
        kwargs[ 'width' ]  = self.w
        kwargs[ 'height' ] = self.h

        super( sm_start_final_state_layout, self ).__init__( *args, bd = 0, highlightthickness = 0, relief = 'ridge', **kwargs )

        self.x = x
        self.y = y
        self.drag_start_x = 0
        self.drag_start_y = 0

        self.grid( row = 0, column = 0, padx = 0, pady = 0 )
        self.place( x = self.x, y = self.y )
        #self.place( x = 0, y = 0 )
        self.initialized = True
        #self.paint()

    def set_border_thickness( self, weight: int ):
        if ( weight == BRD_WEIGHT_THN ):
            self.crnr_size = THN_CRNR_SIZE
        if ( weight == BRD_WEIGHT_MED ):
            self.crnr_size = MED_CRNR_SIZE
        if ( weight == BRD_WEIGHT_THK ):
            self.crnr_size = THK_CRNR_SIZE

        self.w = self.crnr_size * 2
        self.h = self.crnr_size * 2
        self.model[ "layout" ][ "w" ] = self.w
        self.model[ "layout" ][ "h" ] = self.h
        if self.initialized:
            self.config( width = self.w, height = self.h )

    def drag_start( self, event ):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def drag_motion( self, event ):
        new_x = self.winfo_x() - self.drag_start_x + event.x
        # Round it up if closer to next grid point.
        snap_x = new_x + ( GRID_PIX / 2 )
        snap_x = int( snap_x / GRID_PIX )
        snap_x *= GRID_PIX
        
        new_y = self.winfo_y() - self.drag_start_y + event.y
        snap_y = new_y + ( GRID_PIX / 2 )
        snap_y = int( snap_y / GRID_PIX )
        snap_y *= GRID_PIX
        
        self.x = snap_x
        self.y = snap_y
        self.model[ "layout" ][ "x" ] = self.x
        self.model[ "layout" ][ "y" ] = self.y
        self.place( x = self.x, y = self.y )
        global have_changes
        have_changes = True
    
    def paint( self ):
        # Blank out the canvas.
        self.delete( "all" )
        
        self.update_idletasks()

        # Create a simple filled circle.
        # Note: The bottom and right sides of the arc outline box
        #       specify the last position, not last + 1 (as opposed to rectangles).
        circle = self.create_oval( 0, 0, self.w - 1, self.h - 1,
            width = 0, fill = "black", activefill = "darkgreen" )
        # Make it dragable.
        self.tag_bind( circle, sequence = "<Button-1>", func = self.drag_start )
        self.tag_bind( circle, sequence = "<B1-Motion>", func = self.drag_motion )

        # Add a white circle in the center if this is a final state.
        if self.name == HSM_RSVD_FINAL:
            radius = self.crnr_size / 2
            inner_circle = self.create_oval( radius, radius, ( radius * 3 ) - 1, ( radius * 3 ) - 1,
                width = 0, fill = "white", activefill = "lightgreen" )
            # Make it dragable.
            self.tag_bind( inner_circle, sequence = "<Button-1>", func = self.drag_start )
            self.tag_bind( inner_circle, sequence = "<B1-Motion>", func = self.drag_motion )


class sm_state_layout( tk.Canvas ):
    def __init__( self, name, model, x, y, *args, **kwargs ):
        self.model = model
        super( sm_state_layout, self ).__init__( *args, bd = 0, highlightthickness = 0, relief = 'ridge', **kwargs )
        #my_locals = {**locals()}
        #print( f"locals is {my_locals}." )
        self.name = name

        self.x = x
        self.y = y
        self.w = kwargs[ 'width' ]
        self.h = kwargs[ 'height' ]
        self.config( width = self.w, height = self.h )
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.most_wid = -1
        self.most_hgt = -1
        self.prev_wid = -1
        self.prev_hgt = -1

        self.set_border_thickness( BRD_WEIGHT_THN )
        self.grid( row = 0, column = 0, padx = 0, pady = 0 )
        self.place( x = self.x, y = self.y )
        #self.paint()

    def set_border_thickness( self, weight: int ):
        if ( weight == BRD_WEIGHT_THN ):
            self.line_size = THN_LINE_SIZE
            self.crnr_size = THN_CRNR_SIZE
            self.titl_size = THN_TITL_SIZE
        if ( weight == BRD_WEIGHT_MED ):
            self.line_size = MED_LINE_SIZE
            self.crnr_size = MED_CRNR_SIZE
            self.titl_size = MED_TITL_SIZE
        if ( weight == BRD_WEIGHT_THK ):
            self.line_size = THK_LINE_SIZE
            self.crnr_size = THK_CRNR_SIZE
            self.titl_size = THK_TITL_SIZE
        self.paint()

    def drag_start( self, event ):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def drag_motion( self, event ):
        new_x = self.winfo_x() - self.drag_start_x + event.x
        # Round it up if closer to next grid point.
        snap_x = new_x + ( GRID_PIX / 2 )
        snap_x = int( snap_x / GRID_PIX )
        snap_x *= GRID_PIX
        
        new_y = self.winfo_y() - self.drag_start_y + event.y
        snap_y = new_y + ( GRID_PIX / 2 )
        snap_y = int( snap_y / GRID_PIX )
        snap_y *= GRID_PIX
        
        self.x = snap_x
        self.y = snap_y
        self.model[ "layout" ][ "x" ] = self.x
        self.model[ "layout" ][ "y" ] = self.y
        self.place( x = self.x, y = self.y )
        global have_changes
        have_changes = True
    
    def size_start( self, event ):
        curr_wid = self.w
        curr_hgt = self.h
        self.prev_wid = curr_wid
        self.prev_hgt = curr_hgt
        self.most_wid = curr_wid
        self.most_hgt = curr_hgt
        self.offs_wid = curr_wid - event.x
        self.offs_hgt = curr_hgt - event.y

        self.prev_outline = self.create_rectangle(
            0, 0, self.w - 1, self.h - 1,
            outline = "#888888" )
    
    def size_motion( self, event ):
        self.delete( self.prev_outline )
        
        temp_wid = event.x + self.offs_wid
        if temp_wid < MIN_SM_WID:
            temp_wid = MIN_SM_WID
        # Round it up if closer to next grid point.
        snap_x = temp_wid + ( GRID_PIX / 2 )
        snap_x = int( snap_x / GRID_PIX )
        temp_wid = snap_x * GRID_PIX
        self.prev_wid = temp_wid
            
        temp_hgt = event.y + self.offs_wid
        if temp_hgt < MIN_SM_HGT:
            temp_hgt = MIN_SM_HGT
        snap_y = temp_hgt + ( GRID_PIX / 2 )
        snap_y = int( snap_y / GRID_PIX )
        temp_hgt = snap_y * GRID_PIX
        self.prev_hgt = temp_hgt

        # Expand the canvas if going bigger, so the outline can be seen.
        expand = False
        if temp_wid > self.most_wid:
            self.most_wid = temp_wid
            expand = True
        if temp_hgt > self.most_hgt:
            self.most_hgt = temp_hgt
            expand = True
        if expand:
            self.config( width = self.most_wid, height = self.most_hgt )
        #print( f"Mov ({temp_wid},{temp_hgt})" )

        self.prev_outline = self.create_rectangle(
            0, 0, temp_wid - 1, temp_hgt - 1,
            outline = "#888888" )

    def size_stop( self, event ):
        temp_wid = event.x + self.offs_wid
        if temp_wid < MIN_SM_WID:
            temp_wid = MIN_SM_WID
        # Round it up if closer to next grid point.
        snap_x = temp_wid + ( GRID_PIX / 2 )
        snap_x = int( snap_x / GRID_PIX )
        temp_wid = snap_x * GRID_PIX

        temp_hgt = event.y + self.offs_wid
        if temp_hgt < MIN_SM_HGT:
            temp_hgt = MIN_SM_HGT
        snap_y = temp_hgt + ( GRID_PIX / 2 )
        snap_y = int( snap_y / GRID_PIX )
        temp_hgt = snap_y * GRID_PIX

        self.w = temp_wid
        self.h = temp_hgt
        self.model[ "layout" ][ "w" ] = self.w
        self.model[ "layout" ][ "h" ] = self.h
        self.config( width = self.w, height = self.h )
        self.paint()
        global have_changes
        have_changes = True
        
    def paint( self ):
        # Blank out the canvas.
        self.delete( "all" )
        
        self.update_idletasks()

        # Create a rounded rectangle along the edges of this canvas.
        # Note: For widths greater than 1, x and y coordinates relate
        #       to the center of the line or arc.
        top_ctr_y = 0      + ( self.line_size / 2 )
        rgt_ctr_x = self.w - ( self.line_size / 2 )
        btm_ctr_y = self.h - ( self.line_size / 2 )
        lft_ctr_x = 0      + ( self.line_size / 2 )
        # Compute Arc Endpoints
        # Note: The x,y coordinates for the arc are to enclose a full ellipse.
        top_arc_y = 0      + ( self.crnr_size * 2 )
        rgt_arc_x = self.w - ( self.crnr_size * 2 )
        btm_arc_y = self.h - ( self.crnr_size * 2 )
        lft_arc_x = 0      + ( self.crnr_size * 2 )

        # Set up the state name print area.
        title_posn_x = lft_arc_x
        title_posn_y = self.line_size
        title_size_x = rgt_arc_x - lft_arc_x
        title_size_y = self.titl_size
        title_cntr_x = title_posn_x + int( title_size_x / 2 )
        title_cntr_y = title_posn_y + int( title_size_y / 2 )
        title_text = self.create_text( title_cntr_x, title_cntr_y, text = self.name,
            justify = "center", width = 0, activefill = "darkgreen" )
        # Drag the state widget using the title bar.
        self.tag_bind( title_text, sequence = "<Button-1>", func = self.drag_start )
        self.tag_bind( title_text, sequence = "<B1-Motion>", func = self.drag_motion )

        # Resize the state widget using the bottom right corner.
        size_rect = self.create_rectangle(
            rgt_arc_x, btm_arc_y, rgt_ctr_x, btm_ctr_y,
            width = 0,
            activeoutline = "#EEEEEE", activefill = "#EEEEEE" )
        self.tag_bind( size_rect, sequence = "<Button-1>", func = self.size_start )
        self.tag_bind( size_rect, sequence = "<B1-Motion>", func = self.size_motion )
        self.tag_bind( size_rect, sequence = "<ButtonRelease-1>", func = self.size_stop )
        
        # Top Line
        self.create_line(
            0      + self.crnr_size, top_ctr_y,
            self.w - self.crnr_size, top_ctr_y,
            width = self.line_size )
            
        # Upper Right Corner
        # Note: The bottom and right sides of the arc outline box
        #       specify the last position, not last + 1.
        self.create_arc(
            rgt_arc_x    , top_ctr_y    ,
            rgt_ctr_x - 1, top_arc_y - 1,
            start = 0, extent = 90,
            style = 'arc', width = self.line_size )
            
        # Right Line
        self.create_line(
            rgt_ctr_x, 0      + self.crnr_size,
            rgt_ctr_x, self.h - self.crnr_size,
            width = self.line_size )
            
        # Bottom Right Corner
        self.create_arc(
            rgt_arc_x    , btm_arc_y    ,
            rgt_ctr_x - 1, btm_ctr_y - 1,
            start = 270, extent = 90,
            style = 'arc', width = self.line_size )
            
        # Bottom Line
        self.create_line(
            self.w - self.crnr_size, btm_ctr_y,
            0      + self.crnr_size, btm_ctr_y,
            width = self.line_size )
            
        # Bottom Left Corner
        self.create_arc(
            lft_ctr_x    , btm_arc_y    ,
            lft_arc_x - 1, btm_ctr_y - 1,
            start = 180, extent = 90,
            style = 'arc', width = self.line_size )
            
        # Left Line
        self.create_line(
            lft_ctr_x, self.h - self.crnr_size, 
            lft_ctr_x, 0      + self.crnr_size,
            width = self.line_size )
            
        # Top Left Corner
        self.create_arc(
            lft_ctr_x    , top_ctr_y    ,
            lft_arc_x - 1, top_arc_y - 1,
            start = 90, extent = 90,
            style = 'arc', width = self.line_size )
            
        # Section off the title bar.
        self.create_line(
            lft_ctr_x, self.line_size + self.titl_size, 
            rgt_ctr_x, self.line_size + self.titl_size, 
            width = self.line_size )


# The State Machine Layout Widget
class sm_canvas( tk.Canvas ):
    def __init__( self, *args, model = None, **kwargs ):
        super( sm_canvas, self ).__init__( bd = 0, highlightthickness = 0, relief = 'ridge', *args, **kwargs )
        self.model = model
        #print( f"model={self.model}." )

        self.states = []
        for state_name in self.model[ "states" ]:
            state = self.model[ "states" ][ state_name ]
            lft = DEF_STATE_LFT
            top = DEF_STATE_TOP
            wid = DEF_STATE_WID
            hgt = DEF_STATE_HGT
            if ( "layout" in state.keys() ):
                layout = state[ "layout" ]
                if ( "x" in layout.keys() ):
                    lft = layout[ 'x' ]
                if ( "y" in layout.keys() ):
                    top = layout[ 'y' ]
                if ( "w" in layout.keys() ):
                    wid = layout[ 'w' ]
                if ( "h" in layout.keys() ):
                    hgt = layout[ 'h' ]
            else:
                state[ "layout" ] = {
                    "x": lft,
                    "y": top,
                    "w": wid,
                    "h": hgt
                }
            #self.name = self.model.get_new_state_name()
            #print( f"{state_name} @ {lft},{top}-{wid}x{hgt}." )
            
            if state_name == HSM_RSVD_START or state_name == HSM_RSVD_FINAL:
                new_widget = sm_start_final_state_layout( state_name, state, lft, top, bg = 'white' )
                self.states.append( new_widget )
            else:
                new_widget = sm_state_layout( state_name, state, lft, top, width = wid, height = hgt, bg = 'white' )
                self.states.append( new_widget )

    def paint( self ):
        for state in self.states:
            state.paint()
        
            # Then add the transitions.
            #print( f"state.model={state.model}" )
            if state.name == HSM_RSVD_START:
                # Get the transition info.
                assert( HSM_RSVD_TRAN in state.model )
                tran = state.model[ HSM_RSVD_TRAN ]
                assert( len( tran ) == 1 )
                assert( HSM_RSVD_AUTO in tran )
                tran_data = tran[ HSM_RSVD_AUTO ]
                print( f"tran_data={tran_data}" )
                # See if a path is provided.
                path = []
                if HSM_RSVD_PATH in tran_data:
                    for point in tran_data[ HSM_RSVD_PATH ]:
                        path.append( point )
                else:
                    # Path not yet specified. Create a default.
                    pass
            elif state.name == HSM_RSVD_FINAL:
                # The final state can have no transitions out of it.
                assert( HSM_RSVD_TRAN not in state.model )
            else:
                # General case.
                pass

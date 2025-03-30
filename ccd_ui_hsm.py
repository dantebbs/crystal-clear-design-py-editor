import json
import sys
# Note: Tkinter is usually auto-installed with python, but if you get "ImportError: No module named Tkinter":
# python -m pip install python3-tk
import tkinter as tk
from tkinter import ttk
from tkinter import *
#from tkinter.messagebox import showinfo
from PIL import Image, ImageTk
import traceback
import util
# python -m pip install PyYAML
#import yaml

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
HSM_RSVD_STATES = "states"
HSM_RSVD_LYOUT = "layout"
HSM_RSVD_START = "start"
HSM_RSVD_FINAL = "final"
HSM_RSVD_AUTO  = "auto"
HSM_RSVD_TRAN  = "tran"
HSM_RSVD_DEST  = "dest"
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

style = { "Border Weight": BRD_WEIGHT_THN }


def find_canvas_rect( model: object, min_w: int, min_h: int ) -> dict:
    if model:
        # Push extents out as needed.
        ( min_x, min_y ) = ( 0, 0 )
        ( max_x, max_y ) = ( min_w, min_h )
        states = model.get( HSM_RSVD_STATES )
        for state_name, state in states.items():
            layout = state.get( HSM_RSVD_LYOUT )
            if layout:
                state_x = layout.get( "x", DEF_STATE_LFT )
                if ( min_x > state_x ):
                    min_x = state_x
                state_y = layout.get( "y", DEF_STATE_TOP )
                if ( min_y > state_y ):
                    min_y = state_y
                state_w = layout.get( "w", DEF_STATE_WID )
                if ( max_x < state_x + state_w ):
                    max_x = state_x + state_w
                state_h = layout.get( "h", DEF_STATE_HGT )
                if ( max_y < state_y + state_h ):
                    max_y = state_y + state_h

            # TODO: Add recursion to account for sub-states.
            
            # TODO: Add transition paths extent expansion as well.
        
    return { "x": min_x, "y": min_y, "w": max_x - min_x, "h": max_y - min_y }

class sm_state_outline():
    def __init__( self, state: dict ):
        self.lft = DEF_STATE_LFT
        self.top = DEF_STATE_TOP
        self.wid = DEF_STATE_WID
        self.hgt = DEF_STATE_HGT

        layout = state.get( HSM_RSVD_LYOUT )
        if layout:
            if ( "x" in layout.keys() ):
                self.lft = layout[ 'x' ]
            if ( "y" in layout.keys() ):
                self.top = layout[ 'y' ]
            if ( "w" in layout.keys() ):
                self.wid = layout[ 'w' ]
            if ( "h" in layout.keys() ):
                self.hgt = layout[ 'h' ]

        #print( f"{self.lft},{self.top}-{self.wid}x{self.hgt}." )

    def get_path( self ) -> list:
        # Upper Left Corner
        x1 = self.lft
        y1 = self.top
        # Lower Right Corner
        x2 = self.lft + self.wid
        y2 = self.top + self.hgt
        path = [ ( x1, y1 ), ( x2, y1 ), ( x2, y2 ), ( x1, y2 ) ]
        return path

# The Layout Widget for Start and Final States
class sm_start_final_state_layout():
    def __init__( self, parent: object, state_name: str, model: dict ):
        self.initialized = False
        assert( parent )
        assert( type( parent ) == sm_layout )
        self.parent = parent
        assert( state_name )
        assert( state_name == HSM_RSVD_START or state_name == HSM_RSVD_FINAL )
        self.name = state_name
        assert( model )
        self.model = model

        #print( f"start/final model={self.model}." )
        # Set border, which for the start symbol, also sets the width and height.
        self.set_border_thickness( style.get( "Border Weight", BRD_WEIGHT_THN ) )

        # Either read the layout from the model or provide a default one.
        global have_changes

        layout = model.get( HSM_RSVD_LYOUT )
        if layout is None:
            layout = { "x": DEF_STATE_LFT, "y": DEF_STATE_TOP }
            have_changes = True
        
        self.x = layout.get( "x" )
        if self.x is None:
            self.x = DEF_STATE_LFT
            have_changes = True
        self.y = layout.get( "y" )
        if self.y is None:
            self.y = DEF_STATE_TOP
            have_changes = True

        self.initialized = True

    def set_border_thickness( self, weight: int ):
        if ( weight == BRD_WEIGHT_THN ):
            self.crnr_size = THN_CRNR_SIZE
        if ( weight == BRD_WEIGHT_MED ):
            self.crnr_size = MED_CRNR_SIZE
        if ( weight == BRD_WEIGHT_THK ):
            self.crnr_size = THK_CRNR_SIZE

        self.w = self.crnr_size * 2
        self.h = self.crnr_size * 2
        self.model[ HSM_RSVD_LYOUT ][ "w" ] = self.w
        self.model[ HSM_RSVD_LYOUT ][ "h" ] = self.h

    def drag_start( self, event ):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.drag_x = self.x
        self.drag_y = self.y

        #print( f"sm strt_otln = {self.x},{self.y} {self.w}x{self.h}" )
        self.prev_outline = self.parent.canvas.create_rectangle(
            self.x,              self.y,
            self.x + self.w - 1, self.y + self.h - 1,
            outline = "#888888" )
    
    def drag_motion( self, event ):
        new_x = self.x + ( event.x - self.drag_start_x )
        # Round it up if closer to next grid point.
        snap_x = new_x + ( GRID_PIX / 2 )
        snap_x = int( snap_x / GRID_PIX )
        snap_x *= GRID_PIX
        
        new_y = self.y + ( event.y - self.drag_start_y )
        snap_y = new_y + ( GRID_PIX / 2 )
        snap_y = int( snap_y / GRID_PIX )
        snap_y *= GRID_PIX
        
        if snap_x != self.drag_x or snap_y != self.drag_y:
            self.parent.canvas.delete( self.prev_outline )

            self.drag_x = snap_x
            self.drag_y = snap_y
            #print( f"sm new_otln = {self.x},{self.y} {self.w}x{self.h}" )
            self.prev_outline = self.parent.canvas.create_rectangle(
                snap_x,              snap_y,
                snap_x + self.w - 1, snap_y + self.h - 1,
                outline = "#888888" )

            global have_changes
            have_changes = True
            
    def drag_stop( self, event ):
        self.parent.canvas.delete( self.prev_outline )

        if self.x != self.drag_x or self.y != self.drag_y:
            self.x = self.drag_x
            self.y = self.drag_y
            self.model[ HSM_RSVD_LYOUT ][ "x" ] = self.x
            self.model[ HSM_RSVD_LYOUT ][ "y" ] = self.y

            #print( f"sm new_outline {self.x},{self.y},{self.x + self.w},{self.y + self.h}" )
            self.parent.reroute_paths( self )
            self.parent.paint()
    
    def paint( self ):
        #print( f"sm paint canv, {self.name} = {self.x},{self.y} {self.w}x{self.h}" )

        # Create a simple filled circle.
        # Note: The bottom and right sides of the arc outline box
        #       specify the last position, not last + 1 (as opposed to rectangles).
        circle = self.parent.canvas.create_oval(
            self.x + 0,          self.y + 0,
            self.x + self.w - 1, self.y + self.h - 1,
            width = 0, fill = "black", activefill = "darkgreen" )
        # Make it dragable.
        self.parent.canvas.tag_bind( circle, sequence = "<Button-1>", func = self.drag_start )
        self.parent.canvas.tag_bind( circle, sequence = "<B1-Motion>", func = self.drag_motion )
        self.parent.canvas.tag_bind( circle, sequence = "<ButtonRelease-1>", func = self.drag_stop )

        # Add a white circle in the center if this is a final state.
        if self.name == HSM_RSVD_FINAL:
            radius = self.crnr_size / 2
            inner_circle = self.parent.canvas.create_oval(
                self.x + radius,             self.y + radius,
                self.x + ( radius * 3 ) - 1, self.y + ( radius * 3 ) - 1,
                width = 0, fill = "white", activefill = "lightgreen" )
            # Make it dragable.
            self.parent.canvas.tag_bind( inner_circle, sequence = "<Button-1>", func = self.drag_start )
            self.parent.canvas.tag_bind( inner_circle, sequence = "<B1-Motion>", func = self.drag_motion )
            self.parent.canvas.tag_bind( inner_circle, sequence = "<ButtonRelease-1>", func = self.drag_stop )


# The State Layout Widget
class sm_state_layout():
    def __init__( self, parent: object, state_name: str, model: dict ):
        assert( parent )
        assert( type( parent ) == sm_layout )
        self.parent = parent
        assert( state_name )
        self.name = state_name
        assert( model )
        self.model = model

        self.set_border_thickness( style.get( "Border Weight", BRD_WEIGHT_THN ) )

        # Either read the layout from the model or provide a default one.
        global have_changes

        layout = model.get( HSM_RSVD_LYOUT )
        if layout is None:
            layout = { "x": DEF_STATE_LFT, "y": DEF_STATE_TOP, "w": DEF_STATE_WID, "h": DEF_STATE_HGT }
            have_changes = True

        self.x = layout.get( "x", None )
        if self.x is None:
            self.x = DEF_STATE_LFT
            have_changes = True

        self.y = layout.get( "y", None )
        if self.y is None:
            self.y = DEF_STATE_TOP
            have_changes = True

        self.w = layout.get( "w", None )
        if self.w is None:
            self.w = DEF_STATE_WID
            have_changes = True

        self.h = layout.get( "h", None )
        if self.h is None:
            self.h = DEF_STATE_HGT
            have_changes = True

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

    def size_drag_start( self, event ):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.drag_x = self.x
        self.drag_y = self.y

        self.prev_wid = self.w
        self.prev_hgt = self.h
        self.most_wid = self.w
        self.most_hgt = self.h
        self.offs_wid = self.x + self.w - event.x
        self.offs_hgt = self.y + self.h - event.y

        #print( f"sm strt_otln = {self.x},{self.y} {self.w}x{self.h}" )
        self.prev_outline = self.parent.canvas.create_rectangle(
            self.x,              self.y,
            self.x + self.w - 1, self.y + self.h - 1,
            outline = "#888888" )
    
    def drag_motion( self, event ):
        new_x = self.x + ( event.x - self.drag_start_x )
        # Round it up if closer to next grid point.
        snap_x = new_x + ( GRID_PIX / 2 )
        snap_x = int( snap_x / GRID_PIX )
        snap_x *= GRID_PIX
        
        new_y = self.y + ( event.y - self.drag_start_y )
        snap_y = new_y + ( GRID_PIX / 2 )
        snap_y = int( snap_y / GRID_PIX )
        snap_y *= GRID_PIX
        
        if snap_x != self.drag_x or snap_y != self.drag_y:
            self.parent.canvas.delete( self.prev_outline )

            self.drag_x = snap_x
            self.drag_y = snap_y
            #print( f"sm new_otln = {self.x},{self.y} {self.w}x{self.h}" )
            self.prev_outline = self.parent.canvas.create_rectangle(
                snap_x,              snap_y,
                snap_x + self.w - 1, snap_y + self.h - 1,
                outline = "#888888" )

            global have_changes
            have_changes = True
            
    def drag_stop( self, event ):
        self.parent.canvas.delete( self.prev_outline )

        if self.x != self.drag_x or self.y != self.drag_y:
            self.x = self.drag_x
            self.y = self.drag_y
            self.model[ HSM_RSVD_LYOUT ][ "x" ] = self.x
            self.model[ HSM_RSVD_LYOUT ][ "y" ] = self.y

            #print( f"sm new_outline {self.x},{self.y},{self.x + self.w},{self.y + self.h}" )
            self.parent.reroute_paths( self )
            self.parent.paint()
    
    def size_motion( self, event ):
        self.parent.canvas.delete( self.prev_outline )
        
        temp_wid = event.x - self.x + self.offs_wid
        if temp_wid < MIN_SM_WID:
            temp_wid = MIN_SM_WID
        # Round it up if closer to next grid point.
        snap_x = temp_wid + ( GRID_PIX / 2 )
        snap_x = int( snap_x / GRID_PIX )
        temp_wid = snap_x * GRID_PIX
        self.prev_wid = temp_wid
            
        temp_hgt = event.y - self.y + self.offs_wid
        if temp_hgt < MIN_SM_HGT:
            temp_hgt = MIN_SM_HGT
        snap_y = temp_hgt + ( GRID_PIX / 2 )
        snap_y = int( snap_y / GRID_PIX )
        temp_hgt = snap_y * GRID_PIX
        self.prev_hgt = temp_hgt

        #print( f"sm prev_outline {self.x},{self.y},{self.x + temp_wid},{self.y + temp_hgt}" )
        self.prev_outline = self.parent.canvas.create_rectangle(
            self.x + 0,            self.y + 0,
            self.x + temp_wid - 1, self.y + temp_hgt - 1,
            outline = "#888888" )

    def size_stop( self, event ):
        temp_wid = event.x - self.x + self.offs_wid
        if temp_wid < MIN_SM_WID:
            temp_wid = MIN_SM_WID
        # Round it up if closer to next grid point.
        snap_x = temp_wid + ( GRID_PIX / 2 )
        snap_x = int( snap_x / GRID_PIX )
        temp_wid = snap_x * GRID_PIX

        temp_hgt = event.y - self.y + self.offs_wid
        if temp_hgt < MIN_SM_HGT:
            temp_hgt = MIN_SM_HGT
        snap_y = temp_hgt + ( GRID_PIX / 2 )
        snap_y = int( snap_y / GRID_PIX )
        temp_hgt = snap_y * GRID_PIX

        if self.w != temp_wid or self.h != temp_hgt:
            self.w = temp_wid
            self.h = temp_hgt
            self.model[ HSM_RSVD_LYOUT ][ "w" ] = self.w
            self.model[ HSM_RSVD_LYOUT ][ "h" ] = self.h
            #print( f"sm new_outline {self.x},{self.y},{self.x + self.w},{self.y + self.h}" )
            
            self.parent.reroute_paths( self )
            self.parent.paint()
            global have_changes
            have_changes = True
        
    def paint( self ):
        #print( f"sm paint canv, {self.name} = {self.x},{self.y} {self.w}x{self.h}" )

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

        #paint_wid = self.w - 1
        #paint_hgt = self.h - 1
        #self.parent.canvas.create_line( self.x, self.y, self.x + paint_wid, self.y + paint_hgt, width = self.line_size, arrow = "last" )
        #self.parent.canvas.create_line( self.x + paint_wid, self.y, self.x, self.y + paint_hgt, width = self.line_size, arrow = "last" )
        
        # Set up the state name print area.
        title_posn_x = lft_arc_x
        title_posn_y = self.line_size
        title_size_x = rgt_arc_x - lft_arc_x
        title_size_y = self.titl_size
        title_cntr_x = title_posn_x + int( title_size_x / 2 )
        title_cntr_y = title_posn_y + int( title_size_y / 2 )
        title_rect = self.parent.canvas.create_rectangle(
            self.x + title_posn_x, self.y + title_posn_y,
            self.x + title_posn_x + title_size_x, self.y + title_posn_y + title_size_y,
            width = 0,
            activeoutline = "#EEEEEE", activefill = "#EEEEEE" )
        title_text = self.parent.canvas.create_text(
            self.x + title_cntr_x, self.y + title_cntr_y,
            text = self.name, justify = "center", width = 0, activefill = "darkgreen" )
        # Drag the state widget using the title bar.
        self.parent.canvas.tag_bind( title_text, sequence = "<Button-1>", func = self.size_drag_start )
        self.parent.canvas.tag_bind( title_text, sequence = "<B1-Motion>", func = self.drag_motion )
        self.parent.canvas.tag_bind( title_text, sequence = "<ButtonRelease-1>", func = self.drag_stop )

        # Resize the state widget using the bottom right corner.
        size_rect = self.parent.canvas.create_rectangle(
            self.x + rgt_arc_x, self.y + btm_arc_y,
            self.x + rgt_ctr_x, self.y + btm_ctr_y,
            width = 0,
            activeoutline = "#EEEEEE", activefill = "#EEEEEE" )
        self.parent.canvas.tag_bind( size_rect, sequence = "<Button-1>", func = self.size_drag_start )
        self.parent.canvas.tag_bind( size_rect, sequence = "<B1-Motion>", func = self.size_motion )
        self.parent.canvas.tag_bind( size_rect, sequence = "<ButtonRelease-1>", func = self.size_stop )

        # Top Line
        self.parent.canvas.create_line(
            self.x + 0      + self.crnr_size, self.y + top_ctr_y,
            self.x + self.w - self.crnr_size, self.y + top_ctr_y,
            width = self.line_size )
            
        # Upper Right Corner
        # Note: The bottom and right sides of the arc outline box
        #       specify the last position, not last + 1.
        self.parent.canvas.create_arc(
            self.x + rgt_arc_x    , self.y + top_ctr_y    ,
            self.x + rgt_ctr_x - 1, self.y + top_arc_y - 1,
            start = 0, extent = 90,
            style = 'arc', width = self.line_size )
            
        # Right Line
        self.parent.canvas.create_line(
            self.x + rgt_ctr_x, self.y + 0      + self.crnr_size,
            self.x + rgt_ctr_x, self.y + self.h - self.crnr_size,
            width = self.line_size )
            
        # Bottom Right Corner
        self.parent.canvas.create_arc(
            self.x + rgt_arc_x    , self.y + btm_arc_y    ,
            self.x + rgt_ctr_x - 1, self.y + btm_ctr_y - 1,
            start = 270, extent = 90,
            style = 'arc', width = self.line_size )
            
        # Bottom Line
        self.parent.canvas.create_line(
            self.x + self.w - self.crnr_size, self.y + btm_ctr_y,
            self.x + 0      + self.crnr_size, self.y + btm_ctr_y,
            width = self.line_size )
            
        # Bottom Left Corner
        self.parent.canvas.create_arc(
            self.x + lft_ctr_x    , self.y + btm_arc_y    ,
            self.x + lft_arc_x - 1, self.y + btm_ctr_y - 1,
            start = 180, extent = 90,
            style = 'arc', width = self.line_size )
            
        # Left Line
        self.parent.canvas.create_line(
            self.x + lft_ctr_x, self.y + self.h - self.crnr_size, 
            self.x + lft_ctr_x, self.y + 0      + self.crnr_size,
            width = self.line_size )
            
        # Top Left Corner
        self.parent.canvas.create_arc(
            self.x + lft_ctr_x    , self.y + top_ctr_y    ,
            self.x + lft_arc_x - 1, self.y + top_arc_y - 1,
            start = 90, extent = 90,
            style = 'arc', width = self.line_size )
            
        # Section off the title bar.
        self.parent.canvas.create_line(
            self.x + lft_ctr_x, self.y + self.line_size + self.titl_size, 
            self.x + rgt_ctr_x, self.y + self.line_size + self.titl_size, 
            width = self.line_size )

# The State Machine Layout Widget
class sm_layout( tk.Frame ):
    def __init__( self, *args, model: dict = None, **kwargs ):
        #print( f"frm = {self} = {self.winfo_width()}x{self.winfo_height()}+{self.winfo_x()}+{self.winfo_y()}" )
        super( sm_layout, self ).__init__( *args, bd = 0, highlightthickness = 0, relief = 'ridge', **kwargs )
        self.grid( row = 0, column = 0, padx = 0, pady = 0 )
        self.grid_propagate( False )
        self.update()

        # Figure out the canvas size needed.
        # Start with the frame size and then expand if needed by the model.
        canv_w = self.winfo_width()
        canv_h = self.winfo_height()
        canv_geom = find_canvas_rect( model, min_w = canv_w, min_h = canv_h )
        view_str = f"{canv_geom[ "x" ]} {canv_geom[ "y" ]} {canv_geom[ "x" ] + canv_w} {canv_geom[ "y" ] + canv_h}"
        #print( f"F Wrk Frame = {self.winfo_width()}x{self.winfo_height()}" )
        self.canvas = tk.Canvas( master = self, width = canv_geom[ "w" ], height = canv_geom[ "h" ], bd = 0, highlightthickness = 0, relief = 'ridge', scrollregion = view_str )
        self.canvas.grid( row = 0, column = 0, padx = 0, pady = 0 )
        self.canvas.grid_propagate( False )
        self.canvas.update()
        #print( f"C Wrk Frame = {self.canvas.winfo_width()}x{self.canvas.winfo_height()}" )
        curr_border_weight = style.get( "Border Weight", BRD_WEIGHT_THN )
        self.set_border_thickness( curr_border_weight )

        #print( f"Inp model:" )
        #print( json.dumps( model, indent = 2 ) )
        # Since we can't alter a dictionary during iteration, we create a new copy, and use that subsequently.
        self.model = dict( model )

        # Resolve any layout issues for each state.
        self.state_widgets = []
        states = model.get( HSM_RSVD_STATES, {} )
        for state_name, state in states.items():
            self.model[ HSM_RSVD_STATES ][ state_name ] = state
            state_outline = sm_state_outline( state )
            #print( f"{state_name} @ {state_outline.lft},{state_outline.top}-{state_outline.wid}x{state_outline.hgt}." )

            if state_name == HSM_RSVD_START or state_name == HSM_RSVD_FINAL:
                new_widget = sm_start_final_state_layout( self, state_name, state )
                self.state_widgets.append( new_widget )
            else:
                new_widget = sm_state_layout( self, state_name, state )
                self.state_widgets.append( new_widget )

            # Ensure we have at least a default layout for each transition.
            #print( f" {state_name} - {state}" )
            #print( f"{state_name}" )
            transitions = dict( state.get( HSM_RSVD_TRAN ) )
            #print( f"  tr = { transitions }" )
            for transition_name, transition in transitions.items():
                path = transition.get( HSM_RSVD_PATH )
                if path is None:
                    #print( f"1. {state_name} - {state}" )
                    dst_state_name = transition.get( HSM_RSVD_DEST )
                    if dst_state_name:
                        dst_state = model[ HSM_RSVD_STATES ][ dst_state_name ]
                        path = self.find_default_path( state, transition, dst_state )
                        self.model[ HSM_RSVD_STATES ][ state_name ][ HSM_RSVD_TRAN ][ transition_name ][ HSM_RSVD_PATH ] = path
                        global have_changes
                        have_changes = True
                    else:
                        print( f"Transition missing destination { transition_name }: { transition }" )
                        assert( False )
        #print( f"Out model:" )
        #print( json.dumps( self.model, indent = 2 ) )

    def set_border_thickness( self, weight: int ):
        if hasattr( self, "state_widgets" ):
            # Update each of the state widgets.
            for widget in self.state_widgets:
                widget.set_border_thickness( weight )

        # Update the transition lines.
        if ( weight == BRD_WEIGHT_THN ):
            self.line_size = THN_LINE_SIZE
            self.crnr_size = THN_CRNR_SIZE
        if ( weight == BRD_WEIGHT_MED ):
            self.line_size = MED_LINE_SIZE
            self.crnr_size = MED_CRNR_SIZE
        if ( weight == BRD_WEIGHT_THK ):
            self.line_size = THK_LINE_SIZE
            self.crnr_size = THK_CRNR_SIZE

    # This just gives the simplest default path.
    #   Find x and y mid-points on each state.
    #   Pick the shortest pair of midpoints for the first and last points in the path.
    def find_default_path( self, src_state: dict, transition: dict, dst_state: dict ) -> list:
        path = []
        
        # Get the outlines of the states.
        from_outline = sm_state_outline( src_state ).get_path()
        to_outline = sm_state_outline( dst_state ).get_path()
        
        # Duplicate the first point on the end for compute convenience.
        from_outline.append( from_outline[ 0 ] )
        to_outline.append( to_outline[ 0 ] )
        from_midpoints = []
        to_midpoints = []
        for corner_idx in range( len( from_outline ) - 1 ):
            x = int( ( from_outline[ corner_idx ][0] + from_outline[ corner_idx + 1 ][0] ) / 2 )
            y = int( ( from_outline[ corner_idx ][1] + from_outline[ corner_idx + 1 ][1] ) / 2 )
            from_midpoints.append( { "x": x, "y": y } )
            
            x = int( ( to_outline[ corner_idx ][0] + to_outline[ corner_idx + 1 ][0] ) / 2 )
            y = int( ( to_outline[ corner_idx ][1] + to_outline[ corner_idx + 1 ][1] ) / 2 )
            to_midpoints.append( { "x": x, "y": y } )

        if src_state != dst_state:
            # Compute distance between each from_midpoint and each to_midpoint, and find the min.
            from_idx = 0
            min_found = float( 'inf' )
            for from_midpoint in from_midpoints:
                for to_midpoint in to_midpoints:
                    x_delt = to_midpoint[ "x" ] - from_midpoint[ "x" ]
                    y_delt = to_midpoint[ "y" ] - from_midpoint[ "y" ]
                    dist = ( x_delt * x_delt + y_delt * y_delt )
                    if dist < min_found:
                        min_found = dist
                        path = [ from_midpoint, to_midpoint ]
                    from_idx += 1
        else:
            # Special case, a transition to self.
            # Construct a loop on the right side.
            side_idx = 1
            box_size = self.crnr_size * 2
            path = [ from_midpoints[ side_idx ],
              { "x": from_midpoints[ side_idx ][ "x" ] + box_size, "y": from_midpoints[ side_idx ][ "y" ] },
              { "x": from_midpoints[ side_idx ][ "x" ] + box_size, "y": from_midpoints[ side_idx ][ "y" ] + box_size },
              { "x": from_midpoints[ side_idx ][ "x" ],            "y": from_midpoints[ side_idx ][ "y" ] + box_size } ]

        return path

    def paint( self ):
        # Blank out the canvas.
        self.canvas.delete( "all" )
        self.update_idletasks()

        # Size paint area to the current app window size.
        canv_wid = self.winfo_width()
        canv_hgt = self.winfo_height()
        size_rect = self.canvas.create_rectangle(
            0, 0, canv_wid, canv_hgt, width = 0, fill = "white" )
            #, activeoutline = "#EEEEEE", activefill = "#EEEEEE" )
        #canv_wid -= 1
        #canv_hgt -= 1
        #self.canvas.create_line( 0, 0, canv_wid, canv_hgt, width = self.line_size, arrow = "last" )
        #self.canvas.create_line( canv_wid, 0, 0, canv_hgt, width = self.line_size, arrow = "last" )

        for state in self.state_widgets:
            # Paint each state.
            state.paint()
        
            # Then add the transitions.
            #print( f"state.model={state.model}" )
            if state.name == HSM_RSVD_FINAL:
                # The final state can have no transitions out of it.
                assert( HSM_RSVD_TRAN not in state.model )
            else:
                # General case.
                # Get the transition info.
                transitions = state.model.get( HSM_RSVD_TRAN )
                for transition_name, transition in transitions.items():
                    if state.name == HSM_RSVD_START:
                        assert( len( transitions ) == 1 )
                        assert( HSM_RSVD_AUTO in transitions )
                    #print( f"tr paint = {transition}" )
                    # See if a path is provided.
                    path = transition.get( HSM_RSVD_PATH )
                    for point_idx in range( len( path ) - 1 ):
                        src_pt = path[ point_idx + 0 ]
                        dst_pt = path[ point_idx + 1 ]
                        # Regular line segment, vs add arrow to final line segment.
                        arrow = "none"
                        if point_idx == len( path ) - 2:
                            arrow = "last"
                        #print( f'paint sf = {src_pt[ "x" ]}, {src_pt[ "y" ]}, {dst_pt[ "x" ]}, {dst_pt[ "y" ]}, {self.line_size}, {arrow}' )
                        self.canvas.create_line(
                            src_pt[ "x" ], src_pt[ "y" ], 
                            dst_pt[ "x" ], dst_pt[ "y" ], 
                            width = self.line_size, arrow = arrow )

    # This method is for internal use only to facilitate a recursive tree traversal.
    # Call reroute_paths() instead.
    def reroute_changed_paths( self, model: dict ) -> dict:
        changed_model = dict( model )
        #print( json.dumps( model, indent = 2 ) )

        # Check the states at the top level of the model.
        states = model.get( HSM_RSVD_STATES, {} )
        if states:
            for state_name, state in states.items():
                
                # Does this state have the changed_state as a destination?
                #print( f"Checking... {state_name}   against   {self.changed_state.name}" )
                transitions = dict( state.get( HSM_RSVD_TRAN ) )
                for transition_name, transition in transitions.items():
                    path = transition.get( HSM_RSVD_PATH )
                    if path is not None:
                        dst_state_name = transition.get( HSM_RSVD_DEST )
                        if dst_state_name:
                            if dst_state_name == self.changed_state.name:
                                dst_state = model[ HSM_RSVD_STATES ][ dst_state_name ]
                                #print( f"Need to change path from {state_name} to {self.changed_state.name}" )
                                path = self.find_default_path( state, transition, dst_state )
                                changed_model[ HSM_RSVD_STATES ][ state_name ][ HSM_RSVD_TRAN ][ transition_name ][ HSM_RSVD_PATH ] = path
                        else:
                            print( f"Transition missing destination { transition_name }: { transition }" )
                            assert( False )
            changed_model[ HSM_RSVD_STATES ][ state_name ] = state
            
        return changed_model

    def reroute_paths( self, changed_state: object ) -> dict:
        assert( type( changed_state ) == sm_state_layout or type( changed_state ) == sm_start_final_state_layout )
        self.changed_state = changed_state
        #print( f"changed_state = '{self.changed_state.name}'" )
        #print( json.dumps( self.model, indent = 2 ) )
        self.model = self.reroute_changed_paths( self.model )
        #print( json.dumps( self.model, indent = 2 ) )

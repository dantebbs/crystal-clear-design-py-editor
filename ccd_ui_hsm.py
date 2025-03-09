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


class sm_state_outline():
    def __init__( self, state: dict ):
        self.lft = DEF_STATE_LFT
        self.top = DEF_STATE_TOP
        self.wid = DEF_STATE_WID
        self.hgt = DEF_STATE_HGT

        if ( HSM_RSVD_LYOUT in state.keys() ):
            layout = state[ HSM_RSVD_LYOUT ]
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


# The State Layout Widget
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
        self.grid( row = 0, column = 0, padx = 0, pady = 0 )
        self.grid_propagate( False )
        self.update()
        print( f"Wrk Frame w, h = {self.winfo_width()}, {self.winfo_height()}" )
        #print( f"Inp model:" )
        #print( json.dumps( model, indent = 2 ) )
        # Since we can't alter a dictionary during iteration, we create a new copy, and use that subsequently.
        self.model = dict( model )

        # Resolve any layout issues for each state.
        self.state_widgets = []
        for state_name, state in model[ "states" ].items():
            self.model[ "states" ][ state_name ] = state
            state_outline = sm_state_outline( state )
            #print( f"{state_name} @ {state_outline.lft},{state_outline.top}-{state_outline.wid}x{state_outline.hgt}." )

            if state_name == HSM_RSVD_START or state_name == HSM_RSVD_FINAL:
                new_widget = sm_start_final_state_layout( state_name, state,
                  state_outline.lft, state_outline.top, bg = 'white' )
                self.state_widgets.append( new_widget )
            else:
                new_widget = sm_state_layout( state_name, state,
                  state_outline.lft, state_outline.top, width = state_outline.wid, height = state_outline.hgt,
                  bg = 'white' )
                self.state_widgets.append( new_widget )

            # Ensure we have at least a default layout for each transition.
            #print( f"1. {state_name} - {state}" )
            print( f"{state_name}" )
            transitions = dict( state.get( HSM_RSVD_TRAN ) )
            print( f"  tr = { transitions }" )
            for transition_name, transition in transitions.items():
                path = transition.get( HSM_RSVD_LYOUT )
                if path is None:
                    #print( f"1. {state_name} - {state}" )
                    dst_state_name = transition.get( HSM_RSVD_DEST )
                    if dst_state_name:
                        dst_state = model[ "states" ][ dst_state_name ]
                        path = self.find_default_path( state, transition, dst_state )
                        self.model[ "states" ][ state_name ][ HSM_RSVD_TRAN ][ transition_name ][ HSM_RSVD_PATH ] = path
                        global have_changes
                        have_changes = True
                        print( f"  path = {path}" )
                    else:
                        print( f"Transition missing destination { transition_name }: { transition }" )
                        assert( False )
        #print( f"Out model:" )
        #print( json.dumps( self.model, indent = 2 ) )
        self.set_border_thickness( BRD_WEIGHT_THN )

    def set_border_thickness( self, weight: int ):
        # Update each of the state widgets.
        for widget in self.state_widgets:
            widget.set_border_thickness( weight )

        # Update the transation lines.
        if ( weight == BRD_WEIGHT_THN ):
            self.line_size = THN_LINE_SIZE
            self.crnr_size = THN_CRNR_SIZE
        if ( weight == BRD_WEIGHT_MED ):
            self.line_size = MED_LINE_SIZE
            self.crnr_size = MED_CRNR_SIZE
        if ( weight == BRD_WEIGHT_THK ):
            self.line_size = THK_LINE_SIZE
            self.crnr_size = THK_CRNR_SIZE

        self.paint()

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
            path = [ from_midpoints[ 2 ],
              { "x": from_midpoints[ 2 ][ "x" ] + 10, "y": from_midpoints[ 2 ][ "y" ] },
              { "x": from_midpoints[ 2 ][ "x" ] + 10, "y": from_midpoints[ 2 ][ "y" ] + 10 },
              { "x": from_midpoints[ 2 ][ "x" ],      "y": from_midpoints[ 2 ][ "y" ] + 10 } ]

        return path

    def paint( self ):
        # Blank out the canvas.
        self.delete( "all" )
        
        self.update_idletasks()

        # Size paint area to the current app window size.
        print( f"w, h = {self.winfo_width()}, {self.winfo_height()}" )
        size_rect = self.create_rectangle(
            0, 0, self.winfo_width(), self.winfo_height(), width = 0, fill = "white" )
            #, activeoutline = "#EEEEEE", activefill = "#EEEEEE" )

        for state in self.state_widgets:
            # Paint each state.
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
                print( f"paint tr = {tran_data}" )
                # See if a path is provided.
                path = tran_data.get( HSM_RSVD_PATH )
                print( f"paint pa = {path}" )
                for point_idx in range( len( path ) - 1 ):
                    src_pt = path[ point_idx + 0 ]
                    dst_pt = path[ point_idx + 1 ]
                    print( f'paint sf = {src_pt[ "x" ]}, {src_pt[ "y" ]}, {dst_pt[ "x" ]}, {dst_pt[ "y" ]}, {self.line_size}' )
                    self.create_line(
                        src_pt[ "x" ], src_pt[ "y" ], 
                        dst_pt[ "x" ], dst_pt[ "y" ], 
                        width = self.line_size )
            elif state.name == HSM_RSVD_FINAL:
                # The final state can have no transitions out of it.
                assert( HSM_RSVD_TRAN not in state.model )
            else:
                # General case.
                pass

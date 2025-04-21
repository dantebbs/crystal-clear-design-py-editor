import json
import sys
# Note: Tkinter is usually auto-installed with python, but if you get "ImportError: No module named Tkinter":
# python -m pip install python3-tk
import tkinter as tk
from tkinter import ttk
from tkinter import *
#from tkinter.messagebox import showinfo
from PIL import Image, ImageTk
import math
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


# These 3 helper functions check for / find the intersection of lines in a 2-D plane.
def ccw( A: dict, B: dict, C: dict ) -> bool:
    return ( C[ "y" ] - A[ "y" ] ) * ( B[ "x" ] - A[ "x" ] ) > ( B[ "y" ] - A[ "y" ] ) * ( C[ "x" ] - A[ "x" ] )
# Return true if line segments AB and CD intersect
def do_lines_intersect( A: dict, B: dict, C: dict, D: dict ) -> bool:
    #print( f"li: A = {A}\n    B = {B}\n    C = {C}\n    D = {D}" )
    return ccw( A, C, D ) != ccw( B, C, D ) and ccw( A, B, C ) != ccw( A, B, D )

# Return the intersection point if line segments AB and CD intersect, otherwise returns None.
# Formula:
# Given lines (a1, a2) and (b1, b2) and the intersection p
# (if the denominator is zero, the lines have no unique intersection),
#     | | a1 a2 |  a1 - a2 |
#     | | b1 b2 |  b1 - b2 |
# p = ----------------------
#      | a1 - a2  b1 - b2 |
#def line_intersection( a1: dict, a2: dict, b1: dict, b2: dict ) -> dict:
#    xdiff = (a1['x'] - a2['x'], b1['x'] - b2['x'])
#    ydiff = (a1['y'] - a2['y'], b1['y'] - b2['y'])
#
#    def det( j, k ):
#        return j[0] * k[1] - j[1] * k[0]
#
#    div = det( xdiff, ydiff )
#    if div == 0:
#        return None
#
#    #d = ( det( *line1 ), det( *line2 ) )
#    d = ( det( ( a1['x'], a1['y'] ), ( a2['x'], a2['y'] ) ), det( ( b1['x'], b1['y'] ), ( b2['x'], b2['y'] ) ) )
#    x = det( d, xdiff ) / div
#    y = det( d, ydiff ) / div
#    return {'x': x, 'y': y}
    
def line_intersection(line1, line2) -> dict:
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
       return None

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return {'x': int( round( x ) ), 'y': int( round( y ) ) }    

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

        if state:
            layout = state.get( HSM_RSVD_LYOUT )
            if layout:
                if ( 'x' in layout.keys() ):
                    self.lft = layout[ 'x' ]
                if ( 'y' in layout.keys() ):
                    self.top = layout[ 'y' ]
                if ( 'w' in layout.keys() ):
                    self.wid = layout[ 'w' ]
                if ( 'h' in layout.keys() ):
                    self.hgt = layout[ 'h' ]

        #print( f"{self.lft},{self.top}-{self.wid}x{self.hgt}." )

    def get_path( self ) -> list:
        # Upper Left Corner
        x1 = self.lft
        y1 = self.top
        # Lower Right Corner
        x2 = self.lft + self.wid
        y2 = self.top + self.hgt
        path = [ {'x': x1, 'y': y1}, {'x': x2, 'y': y1}, {'x': x2, 'y': y2}, {'x': x1, 'y': y2}, {'x': x1, 'y': y1} ]
        return path

    # Returns a point at x, y coordinates.
    def get_center( self ) -> dict:
        x_ctr = self.lft + ( self.wid / 2 )
        y_ctr = self.top + ( self.hgt / 2 )
        return { 'x': int( round( x_ctr ) ), 'y': int( round( y_ctr ) ) }
    
    # Computes the vector from the center of the state to the given point
    # in polar (magnitude, phase) format.
    def get_vector( self, point: dict ) -> dict:
        center = self.get_center()
        x = point[ 'x' ] - center[ 'x' ]
        y = point[ 'y' ] - center[ 'y' ]
        # Since on-screen, y increases going downward, we'll change to
        # standard cartesian by simply negating y here.
        y = -y
        mag = math.sqrt( ( x * x ) + ( y * y ) )
        pha = math.atan2( y, x )
        return { 'mag': mag, 'pha': pha * ( 180 / math.pi ) }

    # Computes the vector from the center of the state to the closest point
    # (perpendicular intersection) in polar (magnitude, phase) format.
    def get_perpendicular( self, point_a: dict, point_b: dict ) -> dict:
        center = self.get_center()

        # First handle the horizontal and vertical special cases.
        if point_a[ 'x' ] == point_b[ 'x' ]:
            # Horizontal line.
            x = 0
            y = center[ 'y' ] - point_a[ 'y' ]
            mag = math.sqrt( ( x * x ) + ( y * y ) )
            pha = math.atan2( y, x )
            return { 'mag': mag, 'pha': pha }
        elif point_a[ 'y' ] == point_b[ 'y' ]:
            # Vertical line.
            x = center[ 'x' ] - point_a[ 'x' ]
            y = 0
            mag = math.sqrt( ( x * x ) + ( y * y ) )
            pha = math.atan2( y, x )
            return { 'mag': mag, 'pha': pha }
        else:
            x_line = point_b[ 'x' ] - point_a[ 'x' ]
            y_line = point_b[ 'y' ] - point_a[ 'y' ]
            m = y_line / x_line
            b = point_a[ 'y' ] - ( m * point_a[ 'x' ] )
            
            # The perpendicular will have the negative of the reciprocal of the slope.
            m_perp = -1 / m
            # The y-intercept of the perpendicular can be computed using the center.
            b_perp = center[ 'y' ] - ( m_perp * center[ 'x' ] )

            # The system of two equations will have a solution at the
            # intersection point.
            x = ( b_perp - b ) / ( m - m_perp )
            y = m * x + b

        dx = x - center[ 'x' ]
        dy = y - center[ 'y' ]
        # Since on-screen, y increases going downward, we'll change to
        # standard cartesian by simply negating y here.
        dy = -dy
        mag = math.sqrt( ( dx * dx ) + ( dy * dy ) )
        pha = math.atan2( dy, dx )
        vector = { 'mag': mag, 'pha': pha * ( 180 / math.pi ) }
        #print( f"Perp: {dx:.2f},{dy:.2f} = vect {vector}" )
        return vector

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
            state_outline = sm_state_outline( state )
            if state == {}:
                # State had no layout info, use a default.
                state = {'layout': {'x': state_outline.lft, 'y': state_outline.top, 'w': state_outline.wid, 'h': state_outline.hgt }}
            #print( f"state {state_name} = {json.dumps( state, indent = 2 )}." )
            self.model[ HSM_RSVD_STATES ][ state_name ] = state
            #print( f"{state_name} @ {state_outline.lft},{state_outline.top}-{state_outline.wid}x{state_outline.hgt}." )

            if state_name == HSM_RSVD_START or state_name == HSM_RSVD_FINAL:
                new_widget = sm_start_final_state_layout( self, state_name, state )
                self.state_widgets.append( new_widget )
            else:
                new_widget = sm_state_layout( self, state_name, state )
                self.state_widgets.append( new_widget )

            # Ensure we have at least a default layout for each transition.
            #print( f" {state_name} - {state}" )
            if state.get( HSM_RSVD_TRAN ):
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

    # This method checks a path against the current positions of the states, and
    # if there are any transition line segments passing through another state,
    # new segments are added such that the path goes around.
    def find_clean_path( self, path: list ) -> list:
        clean_path = []
        for point_idx in range( len( path ) - 1 ):
            # Check the path against each state machine.
            # Points A and B will be the path segment.
            A = path[ point_idx ]
            clean_path.append( A )
            B = path[ point_idx + 1 ]
            for state_name, state in self.model.get( HSM_RSVD_STATES, {} ).items():
                #print( f"{state_name} = {json.dumps( state, indent = 2 )}" )
                state_outline = sm_state_outline( state ).get_path()
                intersections = []
                for state_corner_idx in range( len( state_outline ) - 1 ):
                    # Points C and D will be an edge on the state outline.
                    C = state_outline[ state_corner_idx ]
                    D = state_outline[ state_corner_idx  + 1 ]
                    if do_lines_intersect( A, B, C, D ):
                        #intersect_point = line_intersection( ( (A['x'], A['y']), (B['x'], B['y']) ),
                        #            ( (C['x'], C['y']), (D['x'], D['y']) ) )
                        #if intersect_point:
                        #    #print( f"Warn: path seg {A},{B} crosses state edge {C},{D}" )
                        #    intersections.append( state_corner_idx )
                        #    #print( f"Warn: path seg {A},{B} crosses state edge #{state_corner_idx}={C},{D} at {intersect_point}" )
                        #    print( f"Warn: path seg {point_idx} crosses state edge #{state_corner_idx}" )
                        #    #vector = sm_state_outline( state ).get_vector( intersect_point )
                        #    #print( f"Warn: vect {vector}" )
                        # Once we know there is an intersection, quit analyzing the state
                        # and add a point. Send it to the most appropriate corner.
                        # Compute the perpendicular between the path line and the
                        # center of the state.
                        vector = sm_state_outline( state ).get_perpendicular( A, B )
                        
                        # Arbitrarily selecting E to be A or B depending on which is left-most.
                        E = A
                        F = B
                        if B[ 'x' ] < A[ 'x' ]:
                            E = B
                            F = A
                        # Push the line away based on quadrant.
                        theta = vector[ 'pha' ]
                        if theta >= -90 and theta < 90:
                            # Cuts through the upper right corner (Quadrant I)
                            # or through the lower right corner (Quadrant IV).
                            clean_path.append( { 'x': F['x'], 'y': E['y'] } )
                        else:
                            # Cuts through the upper left corner (Quadrant II)
                            # or through the lower left corner (Quadrant III).
                            clean_path.append( { 'x': E['x'], 'y': F['y'] } )

                #if len( intersections ) == 2:
                #    # There are 8 cases. 4 cases cut a corner off, and 4 cases cross
                #    # through top and bottom (more left or more right?),
                #    # or left and right (more top or more bottom?).
                #    if ( ( intersections[ 0 ] == 0 ) and ( intersections[ 1 ] == 1 ) ) or
                #        ( ( intersections[ 0 ] == 1 ) and ( intersections[ 1 ] == 0 ) ):
                #        # Cuts through upper right corner.
                #        clean_path.append( { 'x': B['x'], 'y': A['y'] } )
                #    if ( ( intersections[ 0 ] == 1 ) and ( intersections[ 1 ] == 2 ) )
                #        or ( ( intersections[ 0 ] == 2 ) and ( intersections[ 1 ] == 1 ) ):
                #        # Cuts through lower right corner.
                #        clean_path.append( { 'x': B['x'], 'y': A['y'] } )
                #    else if ( intersections[ 0 ] == 2 ) and ( intersections[ 1 ] == 3 ):
                #        # Cuts through lower left corner.
                #        clean_path.append( { 'x': A['x'], 'y': B['y'] } )

        clean_path.append( path[ -1 ] )
        return clean_path

    # This just gives the simplest default path.
    #   Find x and y mid-points on each state.
    #   Pick the shortest pair of midpoints for the first and last points in the path.
    def find_default_path( self, src_state: dict, transition: dict, dst_state: dict ) -> list:
        path = []
        
        # Get the outlines of the states.
        from_outline = sm_state_outline( src_state ).get_path()
        to_outline = sm_state_outline( dst_state ).get_path()
        
        from_midpoints = []
        to_midpoints = []
        for corner_idx in range( len( from_outline ) - 1 ):
            x = int( ( from_outline[ corner_idx ]['x'] + from_outline[ corner_idx + 1 ]['x'] ) / 2 )
            y = int( ( from_outline[ corner_idx ]['y'] + from_outline[ corner_idx + 1 ]['y'] ) / 2 )
            from_midpoints.append( { "x": x, "y": y } )
            
            x = int( ( to_outline[ corner_idx ]['x'] + to_outline[ corner_idx + 1 ]['x'] ) / 2 )
            y = int( ( to_outline[ corner_idx ]['y'] + to_outline[ corner_idx + 1 ]['y'] ) / 2 )
            to_midpoints.append( {'x': x, 'y': y} )

        if src_state == dst_state:
            # Special case, a transition to self.
            # Construct a loop on the right side.
            side_idx = 1
            box_size = self.crnr_size * 2
            path = [ from_midpoints[ side_idx ],
              {'x': from_midpoints[ side_idx ]['x'] + box_size, 'y': from_midpoints[ side_idx ]['y'] },
              {'x': from_midpoints[ side_idx ]['x'] + box_size, 'y': from_midpoints[ side_idx ]['y'] + box_size },
              {'x': from_midpoints[ side_idx ]['x'],            'y': from_midpoints[ side_idx ]['y'] + box_size } ]
        else:
            # Compute distance between each from_midpoint and each to_midpoint, and find the min.
            from_idx = 0
            min_found = float( 'inf' )
            for from_midpoint in from_midpoints:
                for to_midpoint in to_midpoints:
                    x_delt = to_midpoint['x'] - from_midpoint['x']
                    y_delt = to_midpoint['y'] - from_midpoint['y']
                    dist = ( x_delt * x_delt + y_delt * y_delt )
                    if dist < min_found:
                        min_found = dist
                        path = [ from_midpoint, to_midpoint ]
                    from_idx += 1
                    
            # If any path segment intersects (passes through) a state, add a point such that
            # the path routes around it.
            path = self.find_clean_path( path )

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
                if transitions:
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
                if state.get( HSM_RSVD_TRAN ):
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

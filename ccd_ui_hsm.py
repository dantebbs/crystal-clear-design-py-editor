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
#import hierarchical_state_machine
import ccd_model
import ccd_ui_select

try:
    import hierarchical_state_machine as hsm
except ImportError:
    print( f"Unable to import module \"hierarchical_state_machine\"." )
    print( f"Run:\npython -m pip install hierarchical_state_machine\n    ... then try again." )
    quit()

import hsm_defaults


# Get the name of this particular code module.
this_module = sys.modules[__name__]


####################################################################################################
# Note: Two variable naming conventions in this module are:
#   (sub_)state = a reference to a dictionary object within the ccd_model.curr_model object.
#   (sub_)state_path = a list of strings (type ccd_state_path) that lead down the hierarchy tree.


####################################################################################################
# Returns a point as an ( x, y ) tuple, where the integers are guaranteed to be moved to the nearest
# point on the regular grid with horizontal and vertical spacing of GRID_PIX.
def snap_to_grid( x: int, y: int ) -> tuple:
    assert( isinstance( x, int ) )
    assert( isinstance( y, int ) )
    
    # Round it up if closer to next grid point.
    rounded_x = x + ( hsm_defaults.GRID_PIX / 2 )
    grids_x = int( rounded_x / hsm_defaults.GRID_PIX )
    snapped_x = grids_x * hsm_defaults.GRID_PIX
    
    rounded_y = y + ( hsm_defaults.GRID_PIX / 2 )
    grids_y = int( rounded_y / hsm_defaults.GRID_PIX )
    snapped_y = grids_y * hsm_defaults.GRID_PIX
    
    return ( snapped_x, snapped_y )
    

####################################################################################################
class sm_state_outline():
    def __init__( self, state: dict ):
        self.state = state
        
    def get_path( self ) -> list:
        ( x1, y1, x2, y2 ) = ccd_model.curr_model.get_state_layout( self.state )
        path = [ {'x': x1, 'y': y1}, {'x': x2, 'y': y1}, {'x': x2, 'y': y2}, {'x': x1, 'y': y2}, {'x': x1, 'y': y1} ]
        return path

    # Returns a point at x, y coordinates.
    def get_center( self ) -> dict:
        ( x1, y1, x2, y2 ) = ccd_model.curr_model.get_state_layout( self.state )
        x_ctr = ( x1 + x2 ) / 2
        y_ctr = ( y1 + y2 ) / 2
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


####################################################################################################
# This class manages the look, style, painting and editing behavior of a single state widget.
class sm_state_layout():
    def __init__( self, parent: object, state_name: str, model: dict ):
        assert( parent )
        assert( type( parent ) == sm_layout )
        self.parent = parent
        assert( state_name )
        self.name = state_name
        assert( model )
        self.model = model
        layout = ccd_model.get_state_layout( self.model )

        # These are used for dragging and resizing.
        self.x1_start = 0
        self.y1_start = 0
        self.x2_start = 0
        self.y2_start = 0

        # Potential future feature of different line widths.
        self.line_size = hsm_defaults.THN_LINE_SIZE
        self.crnr_size = hsm_defaults.THN_CRNR_SIZE
        self.titl_size = hsm_defaults.THN_TITL_SIZE

    def edit_start( self, event ):
        # self.snapped_[x|y] is the current mouse drag / resize point, but on grid.
        ( self.snapped_x, self.snapped_y ) = snap_to_grid( event.x, event.y )
        self.drag_x_start = self.snapped_x
        self.drag_y_start = self.snapped_y

        ( self.x1_start,
          self.y1_start,
          self.x2_start,
          self.y2_start ) = ccd_model.get_state_layout( self.model )

        #print( f"sm start drag = {self.x1_start},{self.y1_start}" )
        self.curr_outline = self.parent.canvas.create_rectangle(
            self.x1_start,     self.y1_start,
            self.x2_start - 1, self.y2_start - 1,
            outline = "#888888" )
    
    def drag_motion( self, event ):
        ( new_x, new_y ) = snap_to_grid( event.x, event.y )
        
        # self.snapped_[x|y] is the previous mouse drag / resize point, but on grid.
        if new_x != self.snapped_x or new_y != self.snapped_y:
            self.parent.canvas.delete( self.curr_outline )

            new_x1 = self.x1_start + new_x - self.drag_x_start
            new_y1 = self.y1_start + new_y - self.drag_y_start
            new_x2 = new_x1 + self.x2_start - self.x1_start
            new_y2 = new_y1 + self.y2_start - self.y1_start
            self.curr_outline = self.parent.canvas.create_rectangle(
                new_x1,     new_y1,
                new_x2 - 1, new_y2 - 1,
                outline = "#888888" )

            self.snapped_x = new_x
            self.snapped_y = new_y
            
    def drag_stop( self, event ):
        self.parent.canvas.delete( self.curr_outline )

        ( new_x, new_y ) = snap_to_grid( event.x, event.y )
        
        # self.snapped_[x|y] is the previous mouse drag / resize point, but on grid.
        if new_x != self.drag_x_start or new_y != self.drag_y_start:
            new_x1 = self.x1_start + new_x - self.drag_x_start
            new_y1 = self.y1_start + new_y - self.drag_y_start
            new_x2 = new_x1 + self.x2_start - self.x1_start
            new_y2 = new_y1 + self.y2_start - self.y1_start
            ccd_model.set_state_layout( self.model, ( new_x1, new_y1, new_x2, new_y2 ) )
            #set_layout = ccd_model.get_state_layout( self.model )
            #print( f'sm set {set_layout}' )

            self.parent.reroute_paths( self )
            self.parent.paint()
    
    def size_motion( self, event ):
        ( new_x, new_y ) = snap_to_grid( event.x, event.y )

        # Make sure the resulting size of the window is still valid.
        if ( new_x < self.x1_start + hsm_defaults.SM_OUTLINE_MIN[ 'w' ] ):
            new_x  = self.x1_start + hsm_defaults.SM_OUTLINE_MIN[ 'w' ]
        if ( new_y < self.y1_start + hsm_defaults.SM_OUTLINE_MIN[ 'h' ] ):
            new_y  = self.y1_start + hsm_defaults.SM_OUTLINE_MIN[ 'h' ]
        
        # See if the mouse has moved enough to be on a new grid point.
        if new_x != self.snapped_x or new_y != self.snapped_y:
            self.parent.canvas.delete( self.curr_outline )
        
            self.snapped_x = new_x
            self.snapped_y = new_y
            
            self.curr_outline = self.parent.canvas.create_rectangle(
                self.x1_start, self.y1_start,
                new_x - 1,     new_y - 1,
                outline = "#888888" )

    def size_stop( self, event ):
        self.parent.canvas.delete( self.curr_outline )

        ( new_x, new_y ) = snap_to_grid( event.x, event.y )
        
        # Make sure the resulting size of the window is still valid.
        if ( new_x < self.x1_start + hsm_defaults.SM_OUTLINE_MIN[ 'w' ] ):
            new_x  = self.x1_start + hsm_defaults.SM_OUTLINE_MIN[ 'w' ]
        if ( new_y < self.y1_start + hsm_defaults.SM_OUTLINE_MIN[ 'h' ] ):
            new_y  = self.y1_start + hsm_defaults.SM_OUTLINE_MIN[ 'h' ]
        
        if new_x != self.x2_start or new_y != self.y2_start:
            # Make sure the resulting size of the window is still valid.
            proposed_wid = self.snapped_x - self.x1_start
            proposed_hgt = self.snapped_y - self.y1_start
            if proposed_wid >= hsm_defaults.SM_OUTLINE_MIN[ 'w' ] and proposed_hgt >= hsm_defaults.SM_OUTLINE_MIN[ 'h' ]:
                x1 = self.x1_start
                y1 = self.y1_start
                x2 = new_x
                y2 = new_y
                
                ccd_model.set_state_layout( self.model, ( x1, y1, x2, y2 ) )
                set_layout = ccd_model.get_state_layout( self.model )
                print( f'sm size {set_layout}' )
                self.parent.paint()
        
    def paint( self ):
        ( x1, y1, x2, y2 ) = ccd_model.get_state_layout( self.model )

        # Create a rounded rectangle along the edges of this canvas.
        # Note: For widths greater than 1, x and y coordinates relate
        #       to the center of the line or arc.
        wid = x2 - x1
        hgt = y2 - y1
        top_ctr_y = 0   + ( self.line_size / 2 )
        rgt_ctr_x = wid - ( self.line_size / 2 )
        btm_ctr_y = hgt - ( self.line_size / 2 )
        lft_ctr_x = 0   + ( self.line_size / 2 )
        # Compute Arc Endpoints
        # Note: The x,y coordinates for the arc are to enclose a full ellipse.
        top_arc_y = 0   + ( self.crnr_size * 2 )
        rgt_arc_x = wid - ( self.crnr_size * 2 )
        btm_arc_y = hgt - ( self.crnr_size * 2 )
        lft_arc_x = 0   + ( self.crnr_size * 2 )

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
            x1 + title_posn_x,                y1 + title_posn_y,
            x1 + title_posn_x + title_size_x, y1 + title_posn_y + title_size_y,
            width = 0,
            activeoutline = "#EEEEEE", activefill = "#EEEEEE" )
        title_text = self.parent.canvas.create_text(
            x1 + title_cntr_x, y1 + title_cntr_y,
            text = self.name, justify = "center", width = 0, activefill = "darkgreen" )
        # Drag the state widget using the title bar.
        self.parent.canvas.tag_bind( title_text, sequence = "<Button-1>", func = self.edit_start )
        self.parent.canvas.tag_bind( title_text, sequence = "<B1-Motion>", func = self.drag_motion )
        self.parent.canvas.tag_bind( title_text, sequence = "<ButtonRelease-1>", func = self.drag_stop )

        # Resize the state widget using the bottom right corner.
        size_rect = self.parent.canvas.create_rectangle(
            x1 + rgt_arc_x, y1 + btm_arc_y,
            x1 + rgt_ctr_x, y1 + btm_ctr_y,
            width = 0,
            activeoutline = "#EEEEEE", activefill = "#EEEEEE" )
        self.parent.canvas.tag_bind( size_rect, sequence = "<Button-1>", func = self.edit_start )
        self.parent.canvas.tag_bind( size_rect, sequence = "<B1-Motion>", func = self.size_motion )
        self.parent.canvas.tag_bind( size_rect, sequence = "<ButtonRelease-1>", func = self.size_stop )

        # Top Line
        self.parent.canvas.create_line(
            x1 + self.crnr_size, y1 + top_ctr_y,
            x2 - self.crnr_size, y1 + top_ctr_y,
            width = self.line_size )
            
        # Upper Right Corner
        # Note: The bottom and right sides of the arc outline box
        #       specify the last position, not last + 1.
        self.parent.canvas.create_arc(
            x1 + rgt_arc_x    , y1 + top_ctr_y    ,
            x1 + rgt_ctr_x - 1, y1 + top_arc_y - 1,
            start = 0, extent = 90,
            style = 'arc', width = self.line_size )
            
        # Right Line
        self.parent.canvas.create_line(
            x1 + rgt_ctr_x, y1 + self.crnr_size,
            x1 + rgt_ctr_x, y2 - self.crnr_size,
            width = self.line_size )
            
        # Bottom Right Corner
        self.parent.canvas.create_arc(
            x1 + rgt_arc_x    , y1 + btm_arc_y    ,
            x1 + rgt_ctr_x - 1, y1 + btm_ctr_y - 1,
            start = 270, extent = 90,
            style = 'arc', width = self.line_size )
            
        # Bottom Line
        self.parent.canvas.create_line(
            x2 - self.crnr_size, y1 + btm_ctr_y,
            x1 + self.crnr_size, y1 + btm_ctr_y,
            width = self.line_size )
            
        # Bottom Left Corner
        self.parent.canvas.create_arc(
            x1 + lft_ctr_x    , y1 + btm_arc_y    ,
            x1 + lft_arc_x - 1, y1 + btm_ctr_y - 1,
            start = 180, extent = 90,
            style = 'arc', width = self.line_size )
            
        # Left Line
        self.parent.canvas.create_line(
            x1 + lft_ctr_x, y2 - self.crnr_size, 
            x1 + lft_ctr_x, y1 + self.crnr_size,
            width = self.line_size )
            
        # Top Left Corner
        self.parent.canvas.create_arc(
            x1 + lft_ctr_x    , y1 + top_ctr_y    ,
            x1 + lft_arc_x - 1, y1 + top_arc_y - 1,
            start = 90, extent = 90,
            style = 'arc', width = self.line_size )
            
        # Section off the title bar.
        self.parent.canvas.create_line(
            x1 + lft_ctr_x, y1 + self.line_size + self.titl_size, 
            x1 + rgt_ctr_x, y1 + self.line_size + self.titl_size, 
            width = self.line_size )

# The Layout Widget for Start and Final States
class sm_start_final_state_layout( sm_state_layout ):
    def __init__( self, parent: object, state_name: str, model: ccd_model ):
        super().__init__( parent, state_name, model )
        assert( state_name == hsm_defaults.RSVD_START or state_name == hsm_defaults.RSVD_FINAL )
        
    def drag_start( self, event ):
        return super().edit_start( event )

    def drag_motion( self, event ):
        return super().drag_motion( event )

    def drag_stop( self, event ):
        return super().drag_stop( event )

    def paint( self ):
        #print( f"sm paint canv, {self.name} = {self.x},{self.y} {self.w}x{self.h}" )

        ( x1, y1, x2, y2 ) = ccd_model.get_state_layout( self.model )

        # Create a simple filled circle.
        # Note: The bottom and right sides of the arc outline box
        #       specify the last position, not last + 1 (as opposed to rectangles).
        circle = self.parent.canvas.create_oval(
            x1 + 0, y1 + 0,
            x2 - 1, y2 - 1,
            width = 0, fill = "black", activefill = "darkgreen" )
        # Make it dragable.
        self.parent.canvas.tag_bind( circle, sequence = "<Button-1>", func = self.drag_start )
        self.parent.canvas.tag_bind( circle, sequence = "<B1-Motion>", func = self.drag_motion )
        self.parent.canvas.tag_bind( circle, sequence = "<ButtonRelease-1>", func = self.drag_stop )

        # Add a white circle in the center if this is a final state.
        if self.name == hsm_defaults.RSVD_FINAL:
            radius = self.crnr_size / 2
            inner_circle = self.parent.canvas.create_oval(
                x1 + radius,             y1 + radius,
                x1 + ( radius * 3 ) - 1, y1 + ( radius * 3 ) - 1,
                width = 0, fill = "white", activefill = "lightgreen" )
            # Make it dragable.
            self.parent.canvas.tag_bind( inner_circle, sequence = "<Button-1>", func = self.drag_start )
            self.parent.canvas.tag_bind( inner_circle, sequence = "<B1-Motion>", func = self.drag_motion )
            self.parent.canvas.tag_bind( inner_circle, sequence = "<ButtonRelease-1>", func = self.drag_stop )


####################################################################################################
# This class manages the combined laying out of the workspace canvas, and state machine as a whole.
class sm_layout( tk.Frame ):
    def __init__( self, *args, **kwargs ):
        #print( f"frm = {self} = {self.winfo_width()}x{self.winfo_height()}+{self.winfo_x()}+{self.winfo_y()}" )
        super( sm_layout, self ).__init__( *args, bd = 0, highlightthickness = 0, relief = 'ridge', **kwargs )
        self.grid( row = 0, column = 0, padx = 0, pady = 0 )
        self.grid_propagate( False )
        self.update()

        # Figure out the canvas size needed.
        # Start with the frame size and then expand if needed by the model.
        canv_w = self.winfo_width()
        canv_h = self.winfo_height()
        #print( f"Inp model:" )
        #print( json.dumps( ccd_model.curr_model, indent = 2 ) )
        ( canv_x1, canv_y1, canv_x2, canv_y2 ) = ccd_model.find_paint_rect( ccd_model.curr_model, min_x = 0, min_y = 0, max_x = canv_w, max_y = canv_h )
        #print( f"F Wrk Frame = {self.winfo_width()}x{self.winfo_height()}" )
        view_str = f"{canv_x1} {canv_y1} {canv_x2} {canv_y2}"
        self.canvas = tk.Canvas( master = self, width = canv_x2 - canv_x1, height = canv_y2 - canv_y1, bd = 0, highlightthickness = 0, relief = 'ridge', scrollregion = view_str )
        self.canvas.grid( row = 0, column = 0, padx = 0, pady = 0 )
        self.canvas.grid_propagate( False )
        self.canvas.update()
        #print( f"C Wrk Frame = {self.canvas.winfo_width()}x{self.canvas.winfo_height()}" )
        #self.set_border_thickness( workspace_settings.workspace_settings.get_border_thickness() )
        self.line_size = hsm_defaults.THN_LINE_SIZE
        self.crnr_size = hsm_defaults.THN_CRNR_SIZE

        # Set up a selection resolver to cover the working frame.
        self.selector = ccd_ui_select.ccd_ui_select( working_frame = self, working_model = ccd_model.curr_model )

        # Resolve any layout issues for each state.
        self.state_widgets = []
        sub_states = ccd_model.get_sub_states( ccd_model.curr_model )
        if sub_states:
            for state_name, state in sub_states.items():
                state_outline = sm_state_outline( state )
                #if state == {}:
                #    # State had no layout info, use a default.
                #    state = {'layout': {'x': state_outline.lft, 'y': state_outline.top, 'w': state_outline.wid, 'h': state_outline.hgt }}
                #print( f"state {state_name} = {json.dumps( state, indent = 2 )}." )
                ccd_model.curr_model[ hsm_defaults.RSVD_STATES ][ state_name ] = state
                #print( f"{state_name} @ {state_outline.lft},{state_outline.top}-{state_outline.wid}x{state_outline.hgt}." )

                if state_name == hsm_defaults.RSVD_START or state_name == hsm_defaults.RSVD_FINAL:
                    new_widget = sm_start_final_state_layout( self, state_name, state )
                    self.state_widgets.append( new_widget )
                else:
                    new_widget = sm_state_layout( self, state_name, state )
                    self.state_widgets.append( new_widget )

                # Ensure we have at least a default layout for each transition.
                #print( f" {state_name} - {state}" )
                transitions = ccd_model.get_transitions( state )
                if transitions:
                    #print( f"  tr = { transitions }" )
                    for transition_name, transition in transitions.items():
                        path = transition.get( hsm_defaults.RSVD_PATH )
                        if path is None:
                            #print( f"1. {state_name} - {state}" )
                            dst_state_name = transition.get( hsm_defaults.RSVD_DEST )
                            if dst_state_name:
                                dst_state = ccd_model.curr_model[ hsm_defaults.RSVD_STATES ][ dst_state_name ]
                                path = self.find_default_path( state, transition, dst_state )
                                ccd_model.curr_model[ RSVD_STATES ][ state_name ][ hsm_defaults.RSVD_TRAN ][ transition_name ][ hsm_defaults.RSVD_PATH ] = path
                            else:
                                print( f"Transition missing destination { transition_name }: { transition }" )
                                assert( False )
            #print( f"Out model:" )
            #print( json.dumps( ccd_model.curr_model, indent = 2 ) )

    ## Might add a border thickness feature later.
    #def set_border_thickness( self, weight: int ):
    #    if hasattr( self, "state_widgets" ):
    #        # Update each of the state widgets.
    #        for widget in self.state_widgets:
    #            widget.set_border_thickness( weight )
    #
    #    # Update the transition lines.
    #    if ( weight == workspace_settings.BRD_WEIGHT_THN ):
    #        self.line_size = hsm_defaults.THN_LINE_SIZE
    #        self.crnr_size = hsm_defaults.THN_CRNR_SIZE
    #    if ( weight == workspace_settings.BRD_WEIGHT_MED ):
    #        self.line_size = hsm_defaults.MED_LINE_SIZE
    #        self.crnr_size = hsm_defaults.MED_CRNR_SIZE
    #    if ( weight == workspace_settings.BRD_WEIGHT_THK ):
    #        self.line_size = hsm_defaults.THK_LINE_SIZE
    #        self.crnr_size = hsm_defaults.THK_CRNR_SIZE

    # This method checks a path against the current positions of the states, and
    # if there are any transition line segments passing through another state,
    # new segments are added such that the path goes around.
    # TODO: This is going to be 10 or 100 times more complex to get working than
    # anticipated. New plan is to require manual placement for now.
    #path = self.find_clean_path( path )
    #def find_clean_path( self, path: list ) -> list:
    #    clean_path = []
    #    for point_idx in range( len( path ) - 1 ):
    #        # Check the path against each state machine.
    #        # Points A and B will be the path segment.
    #        A = path[ point_idx ]
    #        clean_path.append( A )
    #        B = path[ point_idx + 1 ]
    #        for state_name, state in ccd_model.curr_model.get( RSVD_STATES, {} ).items():
    #            #print( f"{state_name} = {json.dumps( state, indent = 2 )}" )
    #            state_outline = sm_state_outline( state ).get_path()
    #            intersections = []
    #            for state_corner_idx in range( len( state_outline ) - 1 ):
    #                # Points C and D will be an edge on the state outline.
    #                C = state_outline[ state_corner_idx ]
    #                D = state_outline[ state_corner_idx  + 1 ]
    #                if do_lines_intersect( A, B, C, D ):
    #                    # Once we know there is an intersection, quit analyzing the state
    #                    # and add a point. Send it to the most appropriate corner.
    #                    # Compute the perpendicular between the path line and the
    #                    # center of the state.
    #                    vector = sm_state_outline( state ).get_perpendicular( A, B )
    #                    
    #                    # Arbitrarily selecting E to be A or B depending on which is left-most.
    #                    E = A
    #                    F = B
    #                    if B[ 'x' ] < A[ 'x' ]:
    #                        E = B
    #                        F = A
    #                    # Push the line away based on quadrant.
    #                    theta = vector[ 'pha' ]
    #                    if theta >= -90 and theta < 90:
    #                        # Cuts through the upper right corner (Quadrant I)
    #                        # or through the lower right corner (Quadrant IV).
    #                        clean_path.append( { 'x': F['x'], 'y': E['y'] } )
    #                    else:
    #                        # Cuts through the upper left corner (Quadrant II)
    #                        # or through the lower left corner (Quadrant III).
    #                        clean_path.append( { 'x': E['x'], 'y': F['y'] } )
    #                        
    #                    continue
    #
    #    clean_path.append( path[ -1 ] )
    #    return clean_path

    def get_trans_list( self ) -> list:
        transition_list = []
        # Start at the top level of the model.
        states = ccd_model.curr_model.get( hsm_defaults.RSVD_STATES, {} )
        if states:
            for state_name, state in states.items():
                if state.get( hsm_defaults.RSVD_TRAN ):
                    transitions = dict( state.get( hsm_defaults.RSVD_TRAN ) )
                    for transition_name, transition in transitions.items():
                        transition_list.append( transition )
                        #path = transition.get( RSVD_PATH )
                        #if path is not None:
        return transition_list

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
            # TODO: This is going to be 10 or 100 times more complex to get working than
            # anticipated. New plan is to require manual placement for now.
            #path = self.find_clean_path( path )

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
            if state.name == hsm_defaults.RSVD_FINAL:
                # The final state can have no transitions out of it.
                assert( hsm_defaults.RSVD_TRAN not in state.model )
            else:
                # General case.
                # Get the transition info.
                transitions = state.model.get( hsm_defaults.RSVD_TRAN )
                if transitions:
                    for transition_name, transition in transitions.items():
                        if state.name == hsm_defaults.RSVD_START:
                            assert( len( transitions ) == 1 )
                            assert( hsm_defaults.RSVD_AUTO in transitions )
                        #print( f"tr paint = {transition}" )
                        # See if a path is provided.
                        path = transition.get( hsm_defaults.RSVD_PATH )
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
        #print( json.dumps( model, indent = 2 ) )

        # Check all states to see if any enter this state.
        
        ## Start at the top level of the model.
        #states = model.get( hsm_defaults.RSVD_STATES, {} )
        #if states:
        #    for state_name, state in states.items():
        #        
        #        # Does this state have the changed_state as a destination?
        #        #print( f"Checking... {state_name}   against   {self.changed_state.name}" )
        #        if state.get( hsm_defaults.RSVD_TRAN ):
        #            transitions = dict( state.get( hsm_defaults.RSVD_TRAN ) )
        #            for transition_name, transition in transitions.items():
        #                path = transition.get( hsm_defaults.RSVD_PATH )
        #                if path is not None:
        #                    dst_state_name = transition.get( hsm_defaults.RSVD_DEST )
        #                    if dst_state_name:
        #                        dst_state = model[ hsm_defaults.RSVD_STATES ][ dst_state_name ]
        #                        if self.changed_state.name == state_name or dst_state_name == self.changed_state.name:
        #                            #print( f"Updating path from {state_name} to {dst_state_name}" )
        #                            path = self.find_default_path( state, transition, dst_state )
        #                            changed_model[ hsm_defaults.RSVD_STATES ][ state_name ][ hsm_defaults.RSVD_TRAN ][ transition_name ][ hsm_defaults.RSVD_PATH ] = path
        #    changed_model[ hsm_defaults.RSVD_STATES ][ state_name ] = state
            
        return changed_model

    def reroute_paths( self, changed_state: object ) -> dict:
        assert( type( changed_state ) is sm_state_layout
             or type( changed_state ) is sm_start_final_state_layout )
        self.changed_state = changed_state
        #print( f"changed_state = '{self.changed_state.name}'" )
        #print( json.dumps( ccd_model.curr_model, indent = 2 ) )

        # !!!! Can't do this! It changes the type from ccd_model_cl to dict! !!!!
        #ccd_model.curr_model = self.reroute_changed_paths( ccd_model.curr_model )

        state_path = [ "Counting Seconds" ]
        #sub_states = ccd_model.curr_model.get_substate_paths( state_path ) # -> list[ ccd_state_path ]
        state = ccd_model.curr_model.get_state_reference( state_path )
        #print( f'state {state_path} = {state}' )
        # An empty list means states at the root/top level.
        sub_states = ccd_model.curr_model.get_substate_paths( [] )
        
        #print( json.dumps( ccd_model.curr_model, indent = 2 ) )

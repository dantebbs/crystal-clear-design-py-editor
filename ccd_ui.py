import json
import os
import sys
# Note: Tkinter is usually auto-installed with python, but if you get "ImportError: No module named Tkinter":
# python -m pip install python3-tk
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import *
#from tkinter.messagebox import showinfo
import workspace_settings
#import hsm_model
import hierarchical_state_machine

try:
    import hierarchical_state_machine as hsm
except ImportError:
    print( f"Unable to import module \"hierarchical_state_machine\"." )
    print( f"Run:\npython -m pip install hierarchical_state_machine\n    ... then try again." )
    quit()


HSM_BLANK_TEMPLATE = """
{
  "events": [
    "timeout_1000ms"
  ],
  "states": {
    "start": {
      "tran": {
        "auto": {
          "dest": "Counting Seconds"
        }
      }
    },
    "Counting Seconds": {
      "entry": [
        "update_display(seconds_counted)"
      ],
      "tran": {
        "timeout_1000ms": {
          "dest": "Counting Seconds"
        }
      }
    }
  }
}
"""
HSM_DEFAULT_FILENAME = "hsm_model.json"

APP_TITLE = "Crystal Clear Design - State Machine Editor"
APP_LOGO    = f"Logo_CCD_32x32.ico"
TOOL_ICON_SELECT = f"Tool_Select_64x64.png"
TOOL_ICON_STARTS = f"Tool_Start_State_64x64.png"
TOOL_ICON_STATEM = f"Tool_State_Machine_64x64.png"
TOOL_ICON_TRANSI = f"Tool_Transition_64x64.png"
TOOL_ICON_STOPST = f"Tool_Stop_State_64x64.png"
EMPTY_SM_JSON = f"{{}}"

TOOL_NAME_SELECT = f"Select"
TOOL_NAME_STARTS = f"StartState"
TOOL_NAME_STATEM = f"StateMachine"
TOOL_NAME_TRANSI = f"Transition"
TOOL_NAME_STOPST = f"StopState"

# Use even numbers for these sizes to avoid misalignments.
BRD_WEIGHT_THN = 0
BRD_WEIGHT_MED = 1
BRD_WEIGHT_THK = 2

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

# Note: This value must be even and > 0.
# Lines are routed on multiples of GRID_PIX / 2, and the corners of states are
# constrained to multiples of GRID_PIX.
GRID_PIX = 10


this_module = sys.modules[__name__]


# The State Machine Widget
class sm_widget( tk.Canvas ):
    def __init__( self, model: object, *args, **kwargs ):
        super( sm_widget, self ).__init__( bd = 0, highlightthickness = 0, relief = 'ridge', *args, **kwargs )
        self.bind( "<Configure>", self.sm_wid_resize_cb )
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.most_wid = -1
        self.most_hgt = -1
        self.prev_wid = -1
        self.prev_hgt = -1
        self.model = model
        #self.name = self.model.get_new_state_name()
        
        self.set_border_thickness( BRD_WEIGHT_THN )
        self.grid( row = 0, column = 0, padx = 0, pady = 0 )
        self.paint()

    # Track widget size & placement.
    def sm_wid_resize_cb( self, event ):
        if event.widget == self:
            self.update_model()

    def update_model( self ):
        return
        
    def set_border_thickness( self, weight: int ):
        if ( weight == BRD_WEIGHT_THN ):
            self.line_size = THN_LINE_SIZE
            self.crnr_size = THN_CRNR_SIZE
            self.titl_size = THN_TITL_SIZE
            self.paint()
        if ( weight == BRD_WEIGHT_MED ):
            self.line_size = MED_LINE_SIZE
            self.crnr_size = MED_CRNR_SIZE
            self.titl_size = MED_TITL_SIZE
            self.paint()
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
        
        self.place( x = snap_x, y = snap_y )
    
    def size_start( self, event ):
        curr_wid = self.winfo_width()
        curr_hgt = self.winfo_height()
        self.prev_wid = curr_wid
        self.prev_hgt = curr_hgt
        self.most_wid = curr_wid
        self.most_hgt = curr_hgt
        self.offs_wid = curr_wid - event.x
        self.offs_hgt = curr_hgt - event.y

        self.prev_outline = self.create_rectangle(
            0, 0, self.winfo_width() - 1, self.winfo_height() - 1,
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

        self.config( width = temp_wid, height = temp_hgt )
        self.paint()
        #self.model.set_sm_width(  event.width )
    
    def paint( self ):
        # Blank out the canvas.
        self.delete( "all" )
        
        # Get the pixel indeces of the bottom-right of the widget.
        self.update_idletasks()
        rgt = self.winfo_width()
        btm = self.winfo_height()

        # Create a rounded rectangle along the edges of this canvas.
        # Note: For widths greater than 1, x and y coordinates relate
        #       to the center of the line or arc.
        top_ctr_y = 0   + ( self.line_size / 2 )
        rgt_ctr_x = rgt - ( self.line_size / 2 )
        btm_ctr_y = btm - ( self.line_size / 2 )
        lft_ctr_x = 0   + ( self.line_size / 2 )
        # Compute Arc Endpoints
        # Note: The x,y coordinates for the arc are to enclose a full ellipse.
        top_arc_y = 0   + ( self.crnr_size * 2 )
        rgt_arc_x = rgt - ( self.crnr_size * 2 )
        btm_arc_y = btm - ( self.crnr_size * 2 )
        lft_arc_x = 0   + ( self.crnr_size * 2 )

        # Drag the state widget using the title bar.
        drag_rect = self.create_rectangle(
            lft_arc_x, self.line_size, rgt_arc_x, self.line_size + self.titl_size,
            outline = "#FFFFFF", fill = "#FFFFFF",
            activeoutline = "#EEEEEE", activefill = "#EEEEEE" )
        self.tag_bind( drag_rect, sequence = "<Button-1>", func = self.drag_start )
        self.tag_bind( drag_rect, sequence = "<B1-Motion>", func = self.drag_motion )
        
        # Resize the state widget using the bottom right corner.
        size_rect = self.create_rectangle(
            rgt_arc_x, btm_arc_y, rgt_ctr_x, btm_ctr_y,
            outline = "#FFFFFF", fill = "#FFFFFF",
            activeoutline = "#EEEEEE", activefill = "#EEEEEE" )
        self.tag_bind( size_rect, sequence = "<Button-1>", func = self.size_start )
        self.tag_bind( size_rect, sequence = "<B1-Motion>", func = self.size_motion )
        self.tag_bind( size_rect, sequence = "<ButtonRelease-1>", func = self.size_stop )
        
        # Top Line
        self.create_line(
            0   + self.crnr_size, top_ctr_y,
            rgt - self.crnr_size, top_ctr_y,
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
            rgt_ctr_x, 0   + self.crnr_size,
            rgt_ctr_x, btm - self.crnr_size,
            width = self.line_size )
            
        # Bottom Right Corner
        self.create_arc(
            rgt_arc_x    , btm_arc_y    ,
            rgt_ctr_x - 1, btm_ctr_y - 1,
            start = 270, extent = 90,
            style = 'arc', width = self.line_size )
            
        # Bottom Line
        self.create_line(
            rgt - self.crnr_size, btm_ctr_y,
            0   + self.crnr_size, btm_ctr_y,
            width = self.line_size )
            
        # Bottom Left Corner
        self.create_arc(
            lft_ctr_x    , btm_arc_y    ,
            lft_arc_x - 1, btm_ctr_y - 1,
            start = 180, extent = 90,
            style = 'arc', width = self.line_size )
            
        # Left Line
        self.create_line(
            lft_ctr_x, btm - self.crnr_size, 
            lft_ctr_x, 0   + self.crnr_size,
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
            
        # Finalize


#class my_filedialog( filedialog.FileDialog ):
#    def __init__( self, master, title=None ):
#        super( filedialog.FileDialog, self ).__init__( self, master, title )
#
#    def asksaveasfilename(**options):
#        "Ask for a filename to save as."
#
#        return SaveAs(**options).show()
#
#class SaveFileDialog( my_filedialog ):
#    """File selection dialog which checks that the file may be created."""
#
#    title = "Save File Selection Dialog"
#
#    def ok_command( self ):
#        file = self.get_selection()
#        if os.path.exists(file):
#            if os.path.isdir(file):
#                self.master.bell()
#                return
#            d = Dialog(self.top,
#                       title="Overwrite Existing File Question",
#                       text="Overwrite existing file %r?" % (file,),
#                       bitmap='questhead',
#                       default=1,
#                       strings=("Yes", "Cancel"))
#            if d.num != 0:
#                return
#        else:
#            head, tail = os.path.split(file)
#            if not os.path.isdir(head):
#                self.master.bell()
#                return
#        self.quit(file)
#
#class SaveAs( filedialog._Dialog ):
#    "Ask for a filename to save as"
#
#    command = "tk_getSaveFile"

class ccd_ui_layout( tk.Tk ):
    def __init__( self, app_args: object, images_folder: str, *args, **kwargs ):
        self.args = app_args
        self.images = images_folder
        self.has_model_changed = False
        
        try:
            self.model = json.loads( HSM_BLANK_TEMPLATE )
        except json.JSONDecodeError as e:
            print( f"ERR: JSONDecodeError, {e.msg}, file=\"{HSM_BLANK_TEMPLATE}\", line = {e.lineno}, col = {e.colno}." )
        
        # Create the app window
        tk.Tk.__init__( self, *args, **kwargs )
        self.title( APP_TITLE )

        # Default to current monitor screen size.
        app_wid = self.winfo_screenwidth()
        app_hgt = self.winfo_screenheight()
        app_lft = 0
        app_top = 0
        app_geom_str = f"{app_wid}x{app_hgt}+{app_lft}+{app_top}"
        # Use screen width and height as defaults in case they are needed.
        self.wksp_settings = workspace_settings.workspace_settings( app_wid, app_hgt )
        
        # If no request for fullscreen, see if geometry was specified.
        if ( self.args.want_fullscreen() == False ):
            if self.args.want_geometry():
                app_geom_str = self.args.get_geometry()
            else:
                # Position it on the screen where it was last placed.
                ( app_wid, app_hgt ) = self.wksp_settings.get_app_size()
                ( app_lft, app_top ) = self.wksp_settings.get_app_posn()
                app_geom_str = f"{app_wid}x{app_hgt}+{app_lft}+{app_top}"

        #print( f"Window = {app_geom_str}" )
        self.geometry( app_geom_str )
        self.resizable( True, True )
        self.iconbitmap( images_folder + APP_LOGO )
        self.minsize( 100, 100 )
        self.bind( "<Configure>", self.win_resize_cb )

        # Menu Buttons
        menu_height = 35
        self.paned_win = tk.PanedWindow( self, width = self.winfo_width(), height = self.winfo_height(), orient = 'vertical', sashwidth = 0 )
        self.paned_win.grid()
        menu_frame = tk.Frame( self.paned_win, width = app_wid, height = menu_height )
        menu_frame.grid( row = 0, column = 0, padx = 0, pady = 0 )
        
        self.button_file = tk.Menubutton( menu_frame, text = "File", indicatoron = False, padx = 10, relief = "raised" )
        self.button_file.grid( row = 0, column = 0 )
        self.file_menu = tk.Menu( self.button_file, tearoff = False )
        self.button_file[ "menu" ] = self.file_menu
        self.file_menu.add_command( label = "Load File"   , command = lambda: self.file_click_cb( "Load File" ) )
        self.file_menu.add_command( label = "Save File"   , command = lambda: self.file_click_cb( "Save File" ) )
        self.file_menu.add_command( label = "Save File as", command = lambda: self.file_click_cb( "Save File as" ) )
        self.file_menu.add_command( label = "Exit"        , command = lambda: self.file_click_cb( "Exit" ) )

        self.button_edit = tk.Menubutton( menu_frame, text = "Edit", indicatoron = False, padx = 10, relief = "raised" )
        self.button_edit.grid( row = 0, column = 1 )
        self.edit_menu = tk.Menu( self.button_edit, tearoff = False )
        self.button_edit[ "menu" ] = self.edit_menu
        self.edit_menu.add_command( label = "Copy" , state = "disabled", command = lambda: self.edit_click_cb( "Copy"  ) )
        self.edit_menu.add_command( label = "Cut"  , state = "disabled", command = lambda: self.edit_click_cb( "Cut"   ) )
        self.edit_menu.add_command( label = "Paste", state = "disabled", command = lambda: self.edit_click_cb( "Paste" ) )
        self.edit_menu.add_command( label = "Undo" , state = "disabled", command = lambda: self.edit_click_cb( "Undo"  ) )
        self.edit_menu.add_command( label = "Redo" , state = "disabled", command = lambda: self.edit_click_cb( "Redo"  ) )
        
        self.button_view = tk.Menubutton( menu_frame, text = "View", indicatoron = False, padx = 10, relief = "raised" )
        self.button_view.grid( row = 0, column = 2 )
        self.view_menu = tk.Menu( self.button_view, tearoff = False )
        self.button_view[ "menu" ] = self.view_menu
        self.view_menu.add_command( label = "All"  , state = "normal", command = lambda: self.view_click_cb( "All"   ) )
        self.view_menu.add_command( label = "State", state = "normal", command = lambda: self.view_click_cb( "State" ) )
        self.view_menu.add_command( label = "JSON" , state = "normal", command = lambda: self.view_click_cb( "JSON"  ) )
        
        self.button_exit = tk.Menubutton( menu_frame, text = "Exit", indicatoron = False, padx = 10, relief = "raised" )
        self.button_exit.bind( sequence = "<Button-1>", func = self.exit_click_cb )
        self.button_exit.grid( row = 0, column = 3 )
        
        self.paned_win.add( menu_frame, minsize = menu_height )

        # Tool Buttons
        self.tool_names = []
        self.tool_icons = []
        self.tool_buttons = []
        tool_width = 64
        paned_sub_win = tk.PanedWindow( self, width = tool_width, height = self.winfo_height() - menu_height, orient = 'horizontal', sashwidth = 0 )
        paned_sub_win.grid()    
        self.tool_frame = tk.Frame( self, width = tool_width, height = app_hgt - menu_height )
        self.tool_frame.grid( row = 0, column = 0, padx = 0, pady = 0 )
        
        self.tool_button_create( TOOL_NAME_SELECT, self.images + TOOL_ICON_SELECT, self.tool_cb_select )
        self.tool_button_create( TOOL_NAME_STARTS, self.images + TOOL_ICON_STARTS, self.tool_cb_starts )
        self.tool_button_create( TOOL_NAME_STATEM, self.images + TOOL_ICON_STATEM, self.tool_cb_statem )
        self.tool_button_create( TOOL_NAME_TRANSI, self.images + TOOL_ICON_TRANSI, self.tool_cb_transi )
        self.tool_button_create( TOOL_NAME_STOPST, self.images + TOOL_ICON_STOPST, self.tool_cb_stopst )

        self.work_frame = tk.Frame( paned_sub_win, width = app_wid - tool_width, background = 'white' )
        paned_sub_win.add( self.tool_frame )
        paned_sub_win.add( self.work_frame )
        self.paned_win.add( paned_sub_win )
        
        self.filename = ""
        self.sm = json.loads( EMPTY_SM_JSON )
        self.dirty = False
        self.selected_tool_idx = -1
        self.tool_button_click( TOOL_NAME_SELECT )
        
        if self.args.have_start_file():
            # See if a file was specified on the command line.
            self.load_file( self.args.get_start_file() )
        else:
            # Otherwise see if a filename is available from the Most Recently Used list.
            mru_filename = self.wksp_settings.get_latest_used_model()
            if mru_filename:
                self.load_file( mru_filename )

        # TODO: For testing only, remove when developed.
        self.test_sm = sm_widget( self.work_frame, width = 100, height = 80, bg = 'white' )
        self.wksp_settings.are_settings_dirty = True

    # Track main app window size & placement.
    def win_resize_cb( self, event ):
        if event.widget == self:
            self.wksp_settings.set_app_width(  event.width )
            self.wksp_settings.set_app_height( event.height )
            self.wksp_settings.set_app_left(   event.x )
            self.wksp_settings.set_app_top(    event.y )

    def get_screen_size( self ):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        return ( screen_width, screen_height )
    
    def run( self ):
        self.mainloop()

    def file_click_cb( self, option_name ):
        print( f"File -> {option_name}" )
        if option_name == "Exit":
            self.quit()

    def edit_click_cb( self, option_name ):
        print( f"Edit -> {option_name}" )

    def view_click_cb( self, option_name ):
        print( f"View -> {option_name}" )

    def exit_click_cb( self, event ):
        print( f"Exit" )
        self.quit()

    def load_file( self, filename: str = "" ):
        # See if the file exists as listed.
        if not os.path.isfile( filename ):
            # File isn't there, can't load it.
            print( f"WARN: File {filename} not found when loading state machine file." )
        else:
            # Deserialize the JSON state machine description.
            try:
                model_file = open( filename, "r" )
                if not model_file:
                    print( f"WARN: There is something wrong with the file {filename}, and it can't be opened." )
                else:
                    try:
                        self.model = json.load( model_file )
                        self.filename = filename
                        self.wksp_settings.set_latest_used_model( filename )
                        print( f"Loaded file = \"{filename}\"." )
                    except json.JSONDecodeError as e:
                        print( f"ERR: JSONDecodeError, {e.msg}, file=\"{filename}\", line = {e.lineno}, col = {e.colno}." )

                    model_file.close()
            except OSError:
                print( f"WARN: There is something wrong with the file {filename}, and it can't be opened." )

    def save_file( self, filename: str = "" ):
        if (filename == "" and not self.has_model_changed):
            # This is a request to save the current model, but there are no changes to save.
            return

        # If no filename is supplied, assume the request is to save the current file.
        filename_to_save = filename
        if (filename_to_save == ""):
            filename_to_save = self.filename
        
        # If no filename was supplied earlier, use a default name and a dialog box.
        if (filename_to_save == ""):
            filename_to_save = HSM_DEFAULT_FILENAME
        
        # Serialize the JSON state machine description.
        try:
            model_filename = filedialog.asksaveasfilename( parent = self,
              title = "Select Save File Name",
              initialdir = ".",
              initialfile = filename_to_save,
              filetypes = (("JSON files","*.json"),("all files","*.*")),
              defaultextension = "json",
              confirmoverwrite = False )
            model_file = open( model_filename, "w" )
            self.wksp_settings.set_latest_used_model( model_filename )
            json.dump( self.model, model_file, ensure_ascii = True, indent = 4 )
            model_file.close()
            self.model_has_changed = False
            # print( f"Saved file = \"{filename_to_save}\"." )
        except OSError:
            print( f"WARN: There is something wrong with the file {filename_to_save}, and it can't be opened for writing." )

    # Tool Buttons
    def tool_button_create( self, tool_name: str, icon_path: str, callback ):
        tool_idx = len( self.tool_buttons )
        self.tool_names.append( tool_name )
        self.tool_icons.append( tk.PhotoImage( file = icon_path ) )
        self.tool_buttons.append( ttk.Button( self.tool_frame, image = self.tool_icons[ tool_idx ] ) )
        self.tool_buttons[ tool_idx ].grid( row = tool_idx, column = 0, padx = 0, pady = 0 )
        self.tool_buttons[ tool_idx ].bind( "<Button-1>", callback )
    
    def tool_button_click( self, new_tool_name: str ):
        tool_name_matched = ""
        tool_idx = 0
        for tool_name in self.tool_names:
            if new_tool_name == tool_name:
                #print( f"<{tool_name}>" )
                if self.selected_tool_idx != -1:
                    # De-select previous tool.
                    self.tool_buttons[ self.selected_tool_idx ].state( [ '!disabled' ] )
                # Select new tool.
                self.tool_buttons[ tool_idx ].state( [ 'disabled' ] )
                self.selected_tool_idx = tool_idx
            tool_idx += 1

    def quit( self ):
        # Save changes to the model.
        self.save_file()
        
        # Save changes to the workspace.
        self.wksp_settings.sync_to_disk()
        
        super().quit()

    def tool_cb_select( self, event ):
        self.tool_button_click( TOOL_NAME_SELECT )

    def tool_cb_starts( self, event ):
        self.tool_button_click( TOOL_NAME_STARTS )
        self.test_sm.set_border_thickness( BRD_WEIGHT_THN )

    def tool_cb_statem( self, event ):
        self.tool_button_click( TOOL_NAME_STATEM )
        self.test_sm.set_border_thickness( BRD_WEIGHT_MED )

    def tool_cb_transi( self, event ):
        self.tool_button_click( TOOL_NAME_TRANSI )
        self.test_sm.set_border_thickness( BRD_WEIGHT_THK )

    def tool_cb_stopst( self, event ):
        self.tool_button_click( TOOL_NAME_STOPST )

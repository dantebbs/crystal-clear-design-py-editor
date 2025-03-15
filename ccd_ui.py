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


this_module = sys.modules[__name__]
ui = None


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
        self.minsize( 200, 200 )
        self.bind( "<Configure>", self.win_resize_cb )

        # Menu Buttons
        menu_height = 25
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
        paned_sub_win = tk.PanedWindow( self, orient = 'horizontal', sashwidth = 0 )
        paned_sub_win.grid()
        self.tool_frame = tk.Frame( paned_sub_win )
        self.tool_frame.grid( row = 0, column = 0, padx = 0, pady = 0 )
        
        self.tool_button_create( TOOL_NAME_SELECT, self.images + TOOL_ICON_SELECT, self.tool_cb_select )
        self.tool_button_create( TOOL_NAME_STARTS, self.images + TOOL_ICON_STARTS, self.tool_cb_starts )
        self.tool_button_create( TOOL_NAME_STATEM, self.images + TOOL_ICON_STATEM, self.tool_cb_statem )
        self.tool_button_create( TOOL_NAME_TRANSI, self.images + TOOL_ICON_TRANSI, self.tool_cb_transi )
        self.tool_button_create( TOOL_NAME_STOPST, self.images + TOOL_ICON_STOPST, self.tool_cb_stopst )
        
        self.tool_frame.update()
        tool_width = self.tool_frame.winfo_width()

        # Working Canvas
        work_frame_wid = app_wid - tool_width - 1
        # Not sure why, but this extra -2 tweak is currently needed to fit the work area corners.
        work_frame_hgt = app_hgt - menu_height - 1 - 2
        print( f"work frame {work_frame_wid},{work_frame_hgt}" )
        self.work_frame = tk.Frame( paned_sub_win, width = work_frame_wid, height = work_frame_hgt, background = 'white' )
        self.work_frame.grid( row = 0, column = 0, padx = 0, pady = 0 )
        self.work_frame.grid_propagate( False )
        self.work_frame.update()

        paned_sub_win.add( self.tool_frame )
        paned_sub_win.add( self.work_frame )
        self.paned_win.add( paned_sub_win )
        
        self.filename = ""
        self.sm = json.loads( EMPTY_SM_JSON )
        self.dirty = False
        self.selected_tool_idx = -1
        self.tool_button_click( TOOL_NAME_SELECT )
        
        self.curr_model_filename = ""
        if self.args.have_start_file():
            # See if a file was specified on the command line.
            self.load_file( self.args.get_start_file() )
        else:
            # Otherwise see if a filename is available from the Most Recently Used list.
            mru_filename = self.wksp_settings.get_latest_used_model()
            if mru_filename:
                self.load_file( mru_filename )

        self.hsm_canvas = ccd_ui_hsm.sm_canvas( self.work_frame, model = self.model, width = work_frame_wid, height = work_frame_hgt )
        self.hsm_canvas.paint()


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
        #print( f"File -> {option_name}" )
        mru_filename = self.wksp_settings.get_latest_used_model()
        if ( mru_filename ):
            mru_path = os.path.normpath( mru_filename )
        else:
            mru_path = HSM_DEFAULT_FILENAME
        mru_path = mru_path.split( os.sep )
        mru_filename = mru_path[ -1 ]
        mru_path = os.sep.join( mru_path[ 0 : -2 ] )
        if option_name == "Load File":
            model_filename = filedialog.askopenfilename( parent = self,
              title = "Select Save File Name",
              initialdir = mru_path,
              initialfile = mru_filename,
              filetypes = (("JSON files","*.json"),("all files","*.*")),
              defaultextension = "json")
            self.load_file( model_filename )
        if option_name == "Exit":
            self.quit()

    def edit_click_cb( self, option_name ):
        print( f"Edit -> {option_name}" )

    def view_click_cb( self, option_name ):
        print( f"View -> {option_name}" )

    def exit_click_cb( self, event ):
        self.quit()

    def load_file( self, filename: str = "" ):
        # See if the file exists as listed.
        if not os.path.isfile( filename ):
            # File isn't there, can't load it.
            print( f"WARN: File \"{filename}\" not found when loading state machine file." )
        else:
            # Deserialize the JSON state machine description.
            try:
                print( f"INFO: Loading project file \"{filename}\"." )
                model_file = open( filename, "r" )
                if not model_file:
                    print( f"WARN: There is something wrong with the file {filename}, and it can't be opened." )
                else:
                    try:
                        self.model = json.load( model_file )
                        self.filename = filename
                        self.wksp_settings.set_latest_used_model( filename )
                        self.curr_model_filename = filename
                    except json.JSONDecodeError as e:
                        print( f"ERR: JSONDecodeError, {e.msg}, file=\"{filename}\", line = {e.lineno}, col = {e.colno}." )

                    model_file.close()
            except OSError:
                print( f"WARN: There is something wrong with the file {filename}, and it can't be opened." )

    def save_file( self, new_filename: str = "" ):
        #print( f"model={self.model}." )
        if (new_filename == "" and not self.has_model_changed and not ccd_ui_hsm.have_changes ):
            # This is a request to save the current model, but there are no changes to save.
            return

        use_dialog = True
        # When the autosave setting is selected, in some cases we can skip the dialog.
        should_auto_save = self.wksp_settings.get_value( [ "settings", "autosave" ], False )

        # If no filename is supplied, assume the request is to save the current file.
        filename_to_save = new_filename
        if (filename_to_save == ""):
            filename_to_save = self.filename
            if ( should_auto_save ):
                use_dialog = False
        
        # If no filename was supplied earlier, supply a default name and a dialog box.
        if (filename_to_save == ""):
            filename_to_save = HSM_DEFAULT_FILENAME

        # Serialize the JSON state machine description.
        try:
            if ( use_dialog ):
                filename_to_save = filedialog.asksaveasfilename( parent = self,
                  title = "Select Save File Name",
                  initialdir = ".",
                  initialfile = filename_to_save,
                  filetypes = (("JSON files","*.json"),("all files","*.*")),
                  defaultextension = "json",
                  confirmoverwrite = False )
            model_file = open( filename_to_save, "w" )
            self.wksp_settings.set_latest_used_model( filename_to_save )
            json.dump( self.model, model_file, ensure_ascii = True, indent = 4 )
            model_file.close()
            self.model_has_changed = False
            print( f"Saved file = \"{filename_to_save}\"." )
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

    def tool_cb_statem( self, event ):
        self.tool_button_click( TOOL_NAME_STATEM )
        #name = self.model.get_new_state_name()

    def tool_cb_transi( self, event ):
        self.tool_button_click( TOOL_NAME_TRANSI )

    def tool_cb_stopst( self, event ):
        self.tool_button_click( TOOL_NAME_STOPST )


################################# For Reference:
#
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

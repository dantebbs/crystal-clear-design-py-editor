import json
import os
import sys
# Note: Tkinter is usually auto-installed with python, but if you get "ImportError: No module named Tkinter":
# python -m pip install python3-tk
import tkinter as tk
from tkinter import ttk
#from tkinter.messagebox import showinfo
import workspace_settings

try:
    import hierarchical_state_machine as hsm
except ImportError:
    print( f"Unable to import module \"hierarchical_state_machine\"." )
    print( f"Run:\npython -m pip install hierarchical_state_machine\n    ... then try again." )
    quit()


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

# Use even numbers for these to avoid misalignments.
SM_LINE_SIZE = 4
SM_CRNR_SIZE = 12

this_module = sys.modules[__name__]


class sm_widget( tk.Canvas ):
    def __init__( self, *args, **kwargs ):
        super( sm_widget, self ).__init__( bd = 0, highlightthickness = 0, relief = 'ridge', *args, **kwargs )
        self.title_size = SM_CRNR_SIZE * 2
        
    def paint( self ):
        # Get the pixel indeces of the bottom-right of the widget.
        self.update_idletasks()
        rgt = self.winfo_width() - 1
        btm = self.winfo_height() - 1

        # Create a rounded rectangle along the edges of this canvas.
        self.create_line(
            SM_CRNR_SIZE, ( SM_LINE_SIZE / 2 ),
            rgt - SM_CRNR_SIZE, ( SM_LINE_SIZE / 2 ),
            width = SM_LINE_SIZE )
        self.create_arc(
            rgt - ( SM_CRNR_SIZE * 2 ), ( SM_LINE_SIZE / 2 ),
            rgt - ( SM_LINE_SIZE / 2 ), ( SM_CRNR_SIZE * 2 ) - 1,
            start = 0, extent = 90,
            style = 'arc', width = SM_LINE_SIZE )
        self.create_line(
            rgt - ( SM_LINE_SIZE / 2 ), SM_CRNR_SIZE,
            rgt - ( SM_LINE_SIZE / 2 ), btm - SM_CRNR_SIZE,
            width = SM_LINE_SIZE )
        self.create_arc(
            rgt - ( SM_CRNR_SIZE * 2 ), btm - ( SM_CRNR_SIZE * 2 ),
            rgt - ( SM_LINE_SIZE / 2 ), btm - ( SM_LINE_SIZE / 2 ),
            start = 270, extent = 90,
            style = 'arc', width = SM_LINE_SIZE )
        self.create_line(
            rgt - SM_CRNR_SIZE, btm - ( SM_LINE_SIZE / 2 ),
            SM_CRNR_SIZE, btm - ( SM_LINE_SIZE / 2 ),
            width = SM_LINE_SIZE )
        self.create_arc(
            ( SM_LINE_SIZE / 2 ), btm - ( SM_CRNR_SIZE * 2 ),
            ( SM_CRNR_SIZE * 2 ), btm - ( SM_LINE_SIZE / 2 ),
            start = 180, extent = 90,
            style = 'arc', width = SM_LINE_SIZE )
        self.create_line(
            ( SM_LINE_SIZE / 2 ), btm - SM_CRNR_SIZE, 
            ( SM_LINE_SIZE / 2 ), SM_CRNR_SIZE,
            width = SM_LINE_SIZE )
        self.create_arc(
            ( SM_LINE_SIZE / 2 ), ( SM_LINE_SIZE / 2 ),
            ( SM_CRNR_SIZE * 2 ), ( SM_CRNR_SIZE * 2 ),
            start = 90, extent = 90,
            style = 'arc', width = SM_LINE_SIZE )
        # Add the title bar.
        self.create_line(
            0  , SM_LINE_SIZE + self.title_size, 
            rgt, SM_LINE_SIZE + self.title_size, 
            width = SM_LINE_SIZE )
        
class ccd_ui_layout( tk.Tk ):
    def __init__( self, app_args: object, images_folder: str, *args, **kwargs ):
        self.args = app_args
        self.images = images_folder
        
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

        print( f"Window = {app_geom_str}" )
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
        
        self.button_exit = tk.Menubutton( menu_frame, text = "Exit", indicatoron = False, padx = 10, relief = "raised" )
        self.button_exit.bind( sequence = "<Button-1>", func = self.exit_click_cb )
        self.button_exit.grid( row = 0, column = 2 )
        
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
            self.load_file( self.args.get_start_file() )
            
        self.test_sm = sm_widget( self.work_frame, width = 100, height = 80, bg = 'white' )
        self.test_sm.grid( row = 0, column = 0, padx = 0, pady = 0 )
        self.test_sm.paint()

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

    def exit_click_cb( self, event ):
        print( f"Exit" )
        self.quit()

    def load_file( self, filename: str ):
        print( f"Start file = \"{filename}\"." )

        # See if the file exists as listed.
        if not os.path.isfile( filename ):
            # File isn't there, can't load it.
            print( f"WARN: File {filename} not found when loading state machine file." )
        else:
            # Deserialize the JSON state machine description.
            try:
                sm_file = open( filename, "r" )
                if not sm_file:
                    print( f"WARN: There is something wrong with the file {filename}, and it can't be opened." )
                else:
                    try:
                        self.sm = json.load( sm_file )
                        self.filename = filename
                    except json.JSONDecodeError as e:
                        print( f"ERR: JSONDecodeError, {e.msg}, file=\"{filename}\", line = {e.lineno}, col = {e.colno}." )

                    sm_file.close()
            except OSError:
                print( f"WARN: There is something wrong with the file {filename}, and it can't be opened." )

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
                print( f"<{tool_name}>" )
                if self.selected_tool_idx != -1:
                    # De-select previous tool.
                    self.tool_buttons[ self.selected_tool_idx ].state( [ '!disabled' ] )
                # Select new tool.
                self.tool_buttons[ tool_idx ].state( [ 'disabled' ] )
                self.selected_tool_idx = tool_idx
            tool_idx += 1

    def quit( self ):
        # Save changes to the workspace.
        self.wksp_settings.sync_to_disk()
        
        super().quit()

    def tool_cb_select( self, event ):
        self.tool_button_click( TOOL_NAME_SELECT )

    def tool_cb_starts( self, event ):
        self.tool_button_click( TOOL_NAME_STARTS )

    def tool_cb_statem( self, event ):
        self.tool_button_click( TOOL_NAME_STATEM )

    def tool_cb_transi( self, event ):
        self.tool_button_click( TOOL_NAME_TRANSI )

    def tool_cb_stopst( self, event ):
        self.tool_button_click( TOOL_NAME_STOPST )

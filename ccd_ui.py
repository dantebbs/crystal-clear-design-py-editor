import os
# Note: Tkinter is usually auto-installed with python, but if you get "ImportError: No module named Tkinter":
# python -m pip install python3-tk
import tkinter as tk
from tkinter import ttk
#from tkinter.messagebox import showinfo
import workspace_settings

'''
import heirarchical_state_machine
try:
    import heirarchical_state_machine
except ImportError:
    print( f"Unable to import module \"hierarchical_state_machine\"." )
    print( f"Run ...\npython -m pip install hierarchical_state_machine\n       ... then try again." )
    quit()
'''

APP_TITLE = "Crystal Clear Design - State Machine Editor"
APP_LOGO    = f"Logo_CCD_32x32.ico"
TOOL_SELECT = f"Tool_Select_64x64.png"
TOOL_STARTS = f"Tool_Start_State_64x64.png"
TOOL_STATEM = f"Tool_State_Machine_64x64.png"
TOOL_TRANSI = f"Tool_Transition_64x64.png"
TOOL_STOPST = f"Tool_Stop_State_64x64.png"


class ccd_ui_action():
    def __init__( self ):
        pass

class ccd_ui_layout( tk.Tk ):
    def __init__( self, app_args: object, images_folder: str, *args, **kwargs ):
        self.args = app_args
        self.images = images_folder
        
        # Create the app window
        tk.Tk.__init__( self, *args, **kwargs )
        self.title( APP_TITLE )

        # Start with current monitor screen size.
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
        #print( f"{self.winfo_width()}, {self.winfo_height()}" )
        paned_win = tk.PanedWindow( self, width = self.winfo_width(), height = self.winfo_height(), orient = 'vertical', sashwidth = 0 )
        paned_win.grid()
        menu_frame = tk.Frame( paned_win, width = app_wid, height = menu_height )
        menu_frame.grid( row = 0, column = 0, padx = 0, pady = 0 )
        
        button_file = ttk.Button( menu_frame, text = "File", command = lambda: print( f"<File>" ) )
        button_file.grid( row = 0, column = 0 )

        button_edit = ttk.Button( menu_frame, text = "Edit", command = lambda: print( f"<Edit>" ) )
        button_edit.grid( row = 0, column = 1 )
        
        button_exit = ttk.Button( menu_frame, text = "Exit", command = self.quit )
        button_exit.grid( row = 0, column = 2 )
        paned_win.add( menu_frame, minsize = menu_height )

        # Tool Buttons
        tool_width = 64
        paned_sub_win = tk.PanedWindow( self, width = tool_width, height = self.winfo_height() - menu_height, orient = 'horizontal', sashwidth = 0 )
        paned_sub_win.grid()    
        tool_frame = tk.Frame( self, width = tool_width, height = app_hgt - menu_height )
        tool_frame.grid( row = 0, column = 0, padx = 0, pady = 0 )
        
        self.select_icon = tk.PhotoImage( file = self.images + TOOL_SELECT )
        #print( f"file = {self.images + TOOL_SELECT}" )
        self.button_select = ttk.Button( tool_frame, image = self.select_icon )
        self.button_select.grid( row = 0, column = 0, padx = 0, pady = 0 )
        self.button_select.bind( '<Button-1>', self.tool_cb_select )

        self.starts_icon = tk.PhotoImage( file = self.images + TOOL_STARTS )
        self.button_starts = ttk.Button( tool_frame, image = self.starts_icon )
        self.button_starts.grid( row = 1, column = 0, padx = 0, pady = 0 )
        self.button_starts.bind( '<Button-1>', self.tool_cb_starts )

        self.statem_icon = tk.PhotoImage( file = self.images + TOOL_STATEM )
        self.button_statem = ttk.Button( tool_frame, image = self.statem_icon )
        self.button_statem.grid( row = 2, column = 0, padx = 0, pady = 0 )
        self.button_statem.bind( '<Button-1>', self.tool_cb_statem )

        self.transi_icon = tk.PhotoImage( file = self.images + TOOL_TRANSI )
        self.button_transi = ttk.Button( tool_frame, image = self.transi_icon )
        self.button_transi.grid( row = 3, column = 0, padx = 0, pady = 0 )
        self.button_transi.bind( '<Button-1>', self.tool_cb_transi )

        self.stopst_icon = tk.PhotoImage( file = self.images + TOOL_STOPST )
        self.button_stopst = ttk.Button( tool_frame, image = self.stopst_icon )
        self.button_stopst.grid( row = 4, column = 0, padx = 0, pady = 0 )
        self.button_stopst.bind( '<Button-1>', self.tool_cb_stopst )

        work_frame = tk.Frame( paned_sub_win, width = app_wid - tool_width, background = 'white' )
        paned_sub_win.add( tool_frame )
        paned_sub_win.add( work_frame )
        paned_win.add( paned_sub_win )

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
        
    def quit( self ):
        # Save changes to the workspace.
        self.wksp_settings.sync_to_disk()
        
        super().quit()

    def tool_cb_select( self, event ):
        print( f"<Select>" )
        self.button_select.background = "white"

    def tool_cb_starts( self, event ):
        print( f"<Start State>" )
        self.button_starts.background = "white"

    def tool_cb_statem( self, event ):
        print( f"<State Machine>" )
        self.button_statem.background = "white"

    def tool_cb_transi( self, event ):
        print( f"<Transition>" )
        self.button_transi.background = "white"

    def tool_cb_stopst( self, event ):
        print( f"<Stop State>" )
        self.button_stopst.background = "white"

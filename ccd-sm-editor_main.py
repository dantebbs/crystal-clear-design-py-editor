import math
import random
import os
import json
# Note: Tkinter is usually auto-installed with python, but if you get "ImportError: No module named Tkinter":
# python -m pip install python3-tk
import tkinter as tk
from tkinter import ttk
#from tkinter.messagebox import showinfo
import workspace_settings


APP_TITLE = "Crystal Clear Design - State Machine Editor"
APP_LOGO = "CCD_Logo_32x32_on_trans.ico"
TOOL_SELECT = "Select_ptr_64x64_w_trans.png" # "Select_ptr.png"


exit_flag = False
root_win = tk.Tk()


def btn_cb_file():
    print( f"<File>" )

def btn_cb_edit():
    print( f"<Edit>" )

def btn_cb_exit():
    global exit_flag
    exit_flag = True

def btn_cb_select():
    print( f"<Select>" )

def window_exit():
    root.destroy()

def main():
    # Create the app window and position it on the screen where it was last placed.
    global root_win  #    root_win = tk.Tk()
    root_win.title( APP_TITLE )

    # Use the current monitor screen size to set maximums.
    screen_width = root_win.winfo_screenwidth()
    screen_height = root_win.winfo_screenheight()
    wksp_settings = workspace_settings.workspace_settings( screen_width, screen_height )
    ( app_wid, app_hgt ) = wksp_settings.get_app_size()
    ( app_lft, app_top ) = wksp_settings.get_app_posn()
    app_geom_str = f"{app_wid}x{app_hgt}+{app_lft}+{app_top}"
    #print( f"geom = {app_geom_str}" )
    root_win.geometry( app_geom_str )
    root_win.resizable( True, True )
    root_win.iconbitmap( APP_LOGO )
    root_win.minsize( 100, 100 )

    # Track main app window size & placement.
    def win_resize_cb( event ):
        if event.widget == root_win:
            wksp_settings.set_app_width(  event.width )
            wksp_settings.set_app_height( event.height )
            wksp_settings.set_app_left(   event.x )
            wksp_settings.set_app_top(    event.y )

    root_win.bind( "<Configure>", win_resize_cb )

    # Menu Buttons
    menu_height = 40
    #print( f"{root_win.winfo_width()}, {root_win.winfo_height()}" )
    paned_win = ttk.PanedWindow( root_win, width = root_win.winfo_width(), height = root_win.winfo_height(), orient = 'vertical' )
    paned_win.grid()
    menu_frame = tk.Frame( paned_win, width = app_wid, height = menu_height )
    menu_frame.grid( row = 0, column = 0, padx = 0, pady = 0 )
    
    button_file = ttk.Button( menu_frame, text = "File", command = btn_cb_file )
    button_file.grid( row = 0, column = 0 )

    button_edit = ttk.Button( menu_frame, text = "Edit", command = btn_cb_edit )
    button_edit.grid( row = 0, column = 1 )
    
    button_exit = ttk.Button( menu_frame, text = "Exit", command = lambda: root_win.quit() )
    button_exit.grid( row = 0, column = 2 )
    paned_win.add( menu_frame )

    # Tool Buttons
    tool_width = 64
    paned_sub_win = ttk.PanedWindow( root_win, width = tool_width, height = root_win.winfo_height() - menu_height, orient = 'horizontal' )
    paned_sub_win.grid()
    
    tool_frame = tk.Frame( root_win, width = tool_width, height = app_hgt - menu_height )
    tool_frame.grid( row = 0, column = 0, padx = 0, pady = 0 )
    select_icon = tk.PhotoImage( file = TOOL_SELECT )
    button_select = ttk.Button( tool_frame, image = select_icon, command = btn_cb_select )
    button_select.grid( row = 0, column = 0, padx = 0, pady = 0 )

    frame4 = tk.Frame( paned_sub_win, width = 300, background = 'white' )
    paned_sub_win.add( tool_frame )
    paned_sub_win.add( frame4 )
    paned_win.add( paned_sub_win )

    # Now the framework takes over.
    root_win.mainloop()

    # Save changes to the workspace.
    wksp_settings.sync_to_disk()
    

if __name__ == "__main__":
    main()


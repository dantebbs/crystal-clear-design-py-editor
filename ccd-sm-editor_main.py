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
IMAGES_FOLDER = "./images/"
APP_LOGO    = f"{IMAGES_FOLDER}Logo_CCD_32x32.ico"
TOOL_SELECT = f"{IMAGES_FOLDER}Tool_Select_64x64.png"
TOOL_STARTS = f"{IMAGES_FOLDER}Tool_Start_State_64x64.png"
TOOL_STATEM = f"{IMAGES_FOLDER}Tool_State_Machine_64x64.png"
TOOL_TRANSI = f"{IMAGES_FOLDER}Tool_Transition_64x64.png"
TOOL_STOPST = f"{IMAGES_FOLDER}Tool_Stop_State_64x64.png"


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

def btn_cb_starts():
    print( f"<Start State>" )

def btn_cb_statem():
    print( f"<State Machine>" )

def btn_cb_transi():
    print( f"<Transition>" )

def btn_cb_stopst():
    print( f"<Stop State>" )

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
    menu_height = 35
    #print( f"{root_win.winfo_width()}, {root_win.winfo_height()}" )
    paned_win = tk.PanedWindow( root_win, width = root_win.winfo_width(), height = root_win.winfo_height(), orient = 'vertical', sashwidth = 0 )
    paned_win.grid()
    menu_frame = tk.Frame( paned_win, width = app_wid, height = menu_height )
    menu_frame.grid( row = 0, column = 0, padx = 0, pady = 0 )
    
    button_file = ttk.Button( menu_frame, text = "File", command = btn_cb_file )
    button_file.grid( row = 0, column = 0 )

    button_edit = ttk.Button( menu_frame, text = "Edit", command = btn_cb_edit )
    button_edit.grid( row = 0, column = 1 )
    
    button_exit = ttk.Button( menu_frame, text = "Exit", command = lambda: root_win.quit() )
    button_exit.grid( row = 0, column = 2 )
    paned_win.add( menu_frame, minsize = menu_height )

    # Tool Buttons
    tool_width = 64
    paned_sub_win = tk.PanedWindow( root_win, width = tool_width, height = root_win.winfo_height() - menu_height, orient = 'horizontal', sashwidth = 0 )
    paned_sub_win.grid()    
    tool_frame = tk.Frame( root_win, width = tool_width, height = app_hgt - menu_height )
    tool_frame.grid( row = 0, column = 0, padx = 0, pady = 0 )
    
    select_icon = tk.PhotoImage( file = TOOL_SELECT )
    button_select = ttk.Button( tool_frame, image = select_icon, command = btn_cb_select )
    button_select.grid( row = 0, column = 0, padx = 0, pady = 0 )

    starts_icon = tk.PhotoImage( file = TOOL_STARTS )
    button_starts = ttk.Button( tool_frame, image = starts_icon, command = btn_cb_starts )
    button_starts.grid( row = 1, column = 0, padx = 0, pady = 0 )

    statem_icon = tk.PhotoImage( file = TOOL_STATEM )
    button_statem = ttk.Button( tool_frame, image = statem_icon, command = btn_cb_statem )
    button_statem.grid( row = 2, column = 0, padx = 0, pady = 0 )

    transi_icon = tk.PhotoImage( file = TOOL_TRANSI )
    button_transi = ttk.Button( tool_frame, image = transi_icon, command = btn_cb_transi )
    button_transi.grid( row = 3, column = 0, padx = 0, pady = 0 )

    stopst_icon = tk.PhotoImage( file = TOOL_STOPST )
    button_stopst = ttk.Button( tool_frame, image = stopst_icon, command = btn_cb_stopst )
    button_stopst.grid( row = 4, column = 0, padx = 0, pady = 0 )

    work_frame = tk.Frame( paned_sub_win, width = app_wid - tool_width, background = 'white' )
    paned_sub_win.add( tool_frame )
    paned_sub_win.add( work_frame )
    paned_win.add( paned_sub_win )

    # Now the framework takes over.
    root_win.mainloop()

    # Save changes to the workspace.
    wksp_settings.sync_to_disk()
    

if __name__ == "__main__":
    main()


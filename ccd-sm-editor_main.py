import os
# Note: Tkinter is usually auto-installed with python, but if you get "ImportError: No module named Tkinter":
# python -m pip install python3-tk
import tkinter as tk
from tkinter import ttk
#from tkinter.messagebox import showinfo
#import workspace_settings
import ccd_ui_layout


IMAGES_FOLDER = "images\\"


exit_flag = False


def main():
    app_path = os.path.dirname( os.path.realpath( __file__ ) )
    images_path = app_path + "\\" + IMAGES_FOLDER
    ui = ccd_ui_layout.ccd_ui_layout( images_path )
    
    # Ready for the framework to take over.
    ui.run()


if __name__ == "__main__":
    main()


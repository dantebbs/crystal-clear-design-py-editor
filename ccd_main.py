import os
import ccd_args
import ccd_ui


IMAGES_FOLDER = "images\\"


ui = None

def window_exit():
    global ui
    if ( ui is not None ):
        ui.quit()
        ui.destroy()

def main():
    args = ccd_args.ccd_args( __file__ )
    
    app_path = os.path.dirname( os.path.realpath( __file__ ) )
    images_path = app_path + "\\" + IMAGES_FOLDER
    global ui
    ui = ccd_ui.ccd_ui_layout( args, images_path )
    ui.protocol( "WM_DELETE_WINDOW", window_exit )

    # Ready for the framework to take over.
    ui.run()


if __name__ == "__main__":
    main()


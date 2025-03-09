import os
import ccd_args
import ccd_ui


IMAGES_FOLDER = "images\\"


def window_exit():
    if ( ccd_ui.ui is not None ):
        ccd_ui.ui.quit()
        ccd_ui.ui.destroy()

def main():
    args = ccd_args.ccd_args( __file__ )
    
    app_path = os.path.dirname( os.path.realpath( __file__ ) )
    images_path = app_path + "\\" + IMAGES_FOLDER
    ccd_ui.ui = ccd_ui.ccd_ui_layout( args, images_path )
    ccd_ui.ui.protocol( "WM_DELETE_WINDOW", window_exit )

    # Ready for the Tk framework to take over.
    ccd_ui.ui.run()


if __name__ == "__main__":
    main()


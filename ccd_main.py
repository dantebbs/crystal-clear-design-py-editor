import os
import ccd_args
import ccd_ui


IMAGES_FOLDER = "images\\"


def main():
    args = ccd_args.ccd_args( __file__ )
    
    app_path = os.path.dirname( os.path.realpath( __file__ ) )
    images_path = app_path + "\\" + IMAGES_FOLDER
    ui = ccd_ui.ccd_ui_layout( args, images_path )
    
    # Ready for the framework to take over.
    ui.run()


if __name__ == "__main__":
    main()


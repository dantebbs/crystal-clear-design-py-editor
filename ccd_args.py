import argparse
import os
import json


DEFAULT_FILENAME = "workspace.json"
DEFAULT_APP_LEFT = 200
DEFAULT_APP_TOP = 100


class ccd_args():
    def __init__( self, app_name: str ):
        self.app_name = app_name

        # Create an argument parser object.
        parser = argparse.ArgumentParser(
            description = "CCD State Machine Editor",
            formatter_class = argparse.RawTextHelpFormatter,
        )

        # Add optional arguments.
        parser.add_argument(
            "-fullscreen",
            #dest = "fullscreen",
            #default = "False",
            action = "store_true",
            help = f"Start in fullscreen mode.\nExample: python {self.app_name} -fullscreen",
        )
        parser.add_argument(
            "-geometry",
            #action = "store_true",
            nargs = 1,
            help = f"Define the window size and location.\nExample: for 800 w x 600 h, left at 200, top at 100:\npython {self.app_name} -geometry \"800x600+200+100\"",
        )
        parser.add_argument(
            "-sm",
            help = f"Specify the state machine to start with.\nExample: python {self.app_name} -sm assembly_process.json "
            )

        ## Allow address with int or hex format.
        #parser.add_argument(
        #    "-a",
        #    type = lambda x: int( x, 0 ),
        #    help = "Specify address (int or hex)"
        #)

        # Parse the command-line arguments
        self.args = parser.parse_args()
        #print( f"self.args = {self.args}" )

    def want_fullscreen( self ) -> bool:
        return self.args.fullscreen

    def want_geometry( self ) -> bool:
        return self.args.geometry

    def get_geometry( self ) -> str:
        result = ""
        if self.args.geometry:
            result = self.args.geometry[ 0 ]
        return result

    def have_start_file( self ) -> bool:
        return self.args.sm
        
    def get_start_file( self ) -> str:
        result = ""
        if self.args.sm:
            result = self.args.sm
        return result
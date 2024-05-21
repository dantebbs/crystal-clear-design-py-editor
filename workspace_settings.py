import io
import os
import json
import pygame


DEFAULT_FILENAME = "workspace.json"
DEFAULT_APP_LEFT = 200
DEFAULT_APP_TOP = 100
DEFAULT_APP_WIN = f"""{{
    "left": {DEFAULT_APP_LEFT},
    "top": {DEFAULT_APP_TOP},
    "width": 0,
    "height": 0
  }}"""
DEFAULT_JSON = f"""{{
  "app_window": {DEFAULT_APP_WIN}
}}
"""
# Default to an arbitrary fraction of width and height of the current monitor if invalid.
DEFAULT_DISPLAY_PERCENT = 60


# Manage the settings which the user wants to keep across development sessions using a JSON data
# file. Default settings are used if either the file or the field is not available.
class workspace_settings:
    # Preconditions:
    # pygame.init() has been called, and pygame.display.set_mode(...) has not yet been called.
    def __init__( self, pygame: object, filename: str = DEFAULT_FILENAME ):
        # Query the size of the monitor.
        # WARNING: This only works if pygame.init() has been called, but
        # pygame.display.set_mode(...) has not yet been called.
        self.pygame = pygame
        self.display_info = self.pygame.display.Info()
        # Select reasonable defaults for when attempted values are invalid.
        self.max_width = int( self.display_info.current_w )
        self.default_width  = int( self.max_width * DEFAULT_DISPLAY_PERCENT / 100 )
        self.max_height = int( self.display_info.current_h )
        self.default_height = int( self.max_height * DEFAULT_DISPLAY_PERCENT / 100 )

        # See if the workspace file exists in the current folder.
        self.settings_filename = filename
        if not os.path.isfile( filename ):
            # File isn't here, create a default workspace in the current folder.
            print( f"WARN: File {filename} not found when loading workspace file." )
            self.create_default_settings()
        
        # Deserialize the JSON settings.
        try:
            sess_file = open( self.settings_filename, "r" )
            if not sess_file:
                print( f"WARN: There is something wrong with the file {self.settings_filename}, and it can't be opened." )
                print( f"WARN: Try deleting the file (or renaming it), and starting with fresh settings." )
                print( f"WARN: Continuing with default settings." )
                self.settings = json.loads( DEFAULT_JSON )
                return

            try:
                self.settings = json.load( sess_file )
            except json.JSONDecodeError as e:
                print( f"ERR: JSONDecodeError, {e.msg}, file=\"{self.settings_filename}\", line = {e.lineno}, col = {e.colno}." )
                self.create_default_settings()
                
            sess_file.close()
            self.set_app_size()
        except FileNotFoundError:
            self.create_default_settings()

        self.are_settings_dirty = False
        #print( f'wid = {self.settings[ "app_window" ][ "width"  ]}, hgt = {self.settings[ "app_window" ][ "height"  ]}' )

    def create_default_settings( self ) -> None:
        # Reset the filename to ensure a valid default.
        self.settings_filename = DEFAULT_FILENAME
        print( f"INFO: Creating default workspace file {self.settings_filename}." )

        try:
            sess_file = open( self.settings_filename, "w" )
            sess_file.write( DEFAULT_JSON )
            sess_file.close()
        except IOError:
            print( f"ERR: Unable to create file {self.settings_filename}" )

        try:
            self.settings = json.loads( DEFAULT_JSON )
        except json.JSONDecodeError as e:
            print( f"ERR: JSONDecodeError, {e.msg}, str=\"{DEFAULT_JSON}\", line = {e.lineno}, col = {e.colno}." )
            self.create_default_settings()
    
    # Write any settings changes to disk.
    def sync_to_disk( self ) -> None:
        print( f"INFO: Updating \"{self.settings_filename}\" to {self.settings}" )
        if ( self.are_settings_dirty ):
            sess_file = open( self.settings_filename, "w" )
            json.dump( self.settings, sess_file, ensure_ascii = True, indent = 4 )
            sess_file.close()
            self.are_settings_dirty = False

    # Read the application window's width from current settings.
    # If valid, return that. If not:
    #   Set the width to a fraction of the monitor resolution on which the
    #   application was started.
    #
    # Preconditions:
    # self.settings is a dictionary which has been populated.
    #
    # Invariants:
    # No settings outside the "app_window" section are modified during this call.
    #
    # Postconditions:
    # width in the settings data is set to a valid width for the display.
    #
    # Returns:
    # A valid width for the display.
    def get_app_width( self ) -> int:
        # Make sure settings have an application window section.
        try:
            app_settings = self.settings[ "app_window" ]
        except KeyError:
            self.set_app_width( width = 0 )

        # Read the width from settings.
        width_str = "0"
        try:
            width_str = str( self.settings[ "app_window" ][ "width" ] )
        except IndexError:
            self.set_app_width( width = 0 )
            width_str = str( self.settings[ "app_window" ][ "width" ] )
            
        width = self.default_width
        try:
            # This form allows for alternate number bases (hex strings).
            width = int( width_str, 0 )
        except ValueError:
            pass

        return width

    # Set the application window's width into current settings.
    # If valid, new value is stored.
    #
    # Preconditions:
    # self.settings is a dictionary which has been populated.
    #
    # Invariants:
    # No settings outside the "app_window" section are modified during this call.
    #
    # Postconditions:
    # width in the settings data is set to a valid width for the display.
    #
    # Returns:
    # A valid width for the display.
    def set_app_width( self, width: int = 0 ) -> None:
        # Make sure settings have an application window section.
        app_settings = {}
        try:
            app_settings = self.settings[ "app_window" ]
        except KeyError:
            app_settings = DEFAULT_APP_WIN
            self.settings[ "app_window" ] = app_settings
            self.are_settings_dirty = True

        if ( width <= 0 or width >= self.max_width ):
            # Invalid width, don't set it.
            
            # See what is already in the settings.
            try:
                curr_width = app_settings[ "width" ]
            except ValueError:
                # Set to the default instead to ensure visibility.
                curr_width = self.default_width
            
            if ( curr_width > 0 and curr_width <= self.max_width ):
                width = curr_width

        if ( width <= 0 or width >= self.max_width ):
            width = self.default_width

        if ( self.settings[ "app_window" ][ "width" ] != width ):
            # Write the width to settings.
            self.settings[ "app_window" ][ "width" ] = width
            self.are_settings_dirty = True

    # Read the application window's height from current settings.
    # If valid, return that. If not:
    #   Set the height to a fraction of the monitor resolution on which the
    #   application was started.
    #
    # Preconditions:
    # self.settings is a dictionary which has been populated.
    #
    # Invariants:
    # No settings outside the "app_window" section are modified during this call.
    #
    # Postconditions:
    # height in the settings data is set to a valid height for the display.
    #
    # Returns:
    # A valid height for the display.
    def get_app_height( self ) -> int:
        # Make sure settings have an application window section.
        try:
            app_settings = self.settings[ "app_window" ]
        except KeyError:
            self.settings[ "app_window" ] = {
                "left": 0,
                "top": 0,
                "height": 0,
                "height": 0 }

        # Read the height from settings.
        height_str = "0"
        try:
            height_str = str( self.settings[ "app_window" ][ "height" ] )
        except IndexError:
            self.settings[ "app_window" ][ "height" ] = height_str
            
        height = self.default_height
        try:
            # This form allows for hex strings.
            height = int( height_str, 0 )
        except ValueError:
            pass

        return height

    # Set the application window's height into current settings.
    # If valid, new value is stored.
    #
    # Preconditions:
    # self.settings is a dictionary which has been populated.
    #
    # Invariants:
    # No settings outside the "app_window" section are modified during this call.
    #
    # Postconditions:
    # height in the settings data is set to a valid height for the display.
    def set_app_height( self, height: int = 0 ) -> None:
        # Make sure settings have an application window section.
        app_settings = {}
        try:
            app_settings = self.settings[ "app_window" ]
        except KeyError:
            app_settings = {
                "left": 0,
                "top": 0,
                "width": 0,
                "height": 0 }
            self.settings[ "app_window" ] = app_settings

        if ( height <= 0 or height >= self.max_height ):
            # Invalid height, don't set it.
            
            # See what is already in the settings.
            try:
                curr_height = app_settings[ "height" ]
            except ValueError:
                # Set to the default instead to ensure visibility.
                curr_height = self.default_height
            
            if ( curr_height > 0 and curr_height <= self.max_height ):
                height = curr_height

        if ( height <= 0 or height >= self.max_height ):
            height = self.default_height

        # Write the height to settings.
        self.settings[ "app_window" ][ "height" ] = height

    # Retrieve the width and height settings for the display.
    #
    # Preconditions:
    # None.
    #
    # Invariants:
    # No other settings are modified during this call.
    #
    # Postconditions:
    # width and height are unchanged if valid, or set to a valid constant.
    # See get_app_width() and get_app_height() for treatment of invalid values.
    #
    # Returns:
    # Valid width and height as a two-tuple where ( width, height ) = latest from set_app_size().
    def get_app_size( self ) -> tuple:
        width = self.get_app_width()
        height = self.get_app_height()
        return ( width, height )

    # Confirm the requested width and height are valid for the display. If valid update the
    # setting(s). If either is invalid, first check the current setting and if valid just
    # keep it. If current and requested are both invalid, set to some fraction of the
    # display/monitor on which the app was opened.
    #
    # Preconditions:
    # None.
    #
    # Invariants:
    # No other settings are modified during this call.
    #
    # Postconditions:
    # width and height are internally set to valid values for the display monitor on which
    # the app was launched.
    #
    # Param:  width  Must be between 1 and monitor-width.
    # Param:  height  Must be between 1 and monitor-height.
    def set_app_size( self, width: int = 0, height: int = 0 ) -> None:
        # Resolve valid application window size.
        self.set_app_width( width )
        self.set_app_height( height )
        """
        # If a zero is passed in, check the current setting to see if it can be used.
        if ( width <= 0 or width > self.max_width ):
            try:
                width = int( str( self.settings[ "app_window" ][ "width" ] ), 0 )
            except ValueError:
                # Set to reasonable value if both passed value and JSON value are invalid.
                width = int( self.display_info.current_w * mon_pct )
            self.settings[ "app_window" ][ "width"  ] = width

        # If a zero is passed in, check the current setting to see if it can be used.
        if ( height <= 0 or height > self.display_info.current_h ):
            try:
                height = int( str( self.settings[ "app_window" ][ "height" ] ), 0 )
            except ValueError:
                # Set to reasonable value if both passed value and JSON value are invalid.
                height = int( self.display_info.current_h * mon_pct )
            self.settings[ "app_window" ][ "height" ] = height
        """

    def get_app_topleft( self ) -> tuple:
        pass

    # Confirm the requested left and top are valid for the display. If valid update the
    # setting(s). If either is invalid, first check the current setting and if valid just
    # keep it. If current and requested are both invalid, set to a fixed value.
    #
    # Preconditions:
    # None.
    #
    # Invariants:
    # No other settings are modified during this call.
    #
    # Postconditions:
    # right and top are internally set to valid values for the display monitor on which
    # the app was launched.
    #
    # Param:  width  Must be between 1 and monitor-width.
    # Param:  height  Must be between 1 and monitor-height.
    def set_app_topleft( self, left: int = -1, top: int = -1 ) -> None:
        pass


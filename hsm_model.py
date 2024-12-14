import io
import os
import json


HSM_DEFAULT_FILENAME = "hsm_model.json"
DEFAULT_SM_REC = f"""{{
    "name": "foo_bar"
  }}"""
DEFAULT_JSON = f"""{{
  "sm_widget": {DEFAULT_SM_REC}
}}
"""


# Manage the settings which the user wants to keep across development sessions using a JSON data
# file. Default settings are used if either the file or the field is not available.
class hsm_model:
    # Preconditions:
    # pygame.init() has been called, and pygame.display.set_mode(...) has not yet been called.
    def __init__( self, screen_max_x: int, screen_max_y: int, filename: str = DEFAULT_FILENAME ):
        # Select reasonable defaults for when attempted values are invalid.
        self.max_width = screen_max_x
        self.default_width  = int( self.max_width * DEFAULT_DISPLAY_PERCENT / 100 )
        self.max_height = screen_max_y
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
            exit()
    
    # Write any settings changes to disk.
    def sync_to_disk( self ) -> None:
        #print( f"INFO: Updating \"{self.settings_filename}\" to {self.settings}" )
        if ( self.are_settings_dirty ):
            sess_file = open( self.settings_filename, "w" )
            json.dump( self.settings, sess_file, ensure_ascii = True, indent = 4 )
            sess_file.close()
            self.are_settings_dirty = False

    # Read a value from current settings.
    # If valid, return that. If not:
    #   Set the width to a fraction of the monitor resolution on which the
    #   application was started.
    #
    # Preconditions:
    # self.settings is a dictionary which has been populated.
    #
    # Invariants:
    # No settings outside the key_chain entry, are modified during this call.
    #
    # Postconditions:
    # Either the pre-call value, or if not yet set, the default value is stored in the settings data.
    #
    # Returns:
    # A valid value, first from settings, or the default if not previously set.
    def get_value( self, key_chain: list, default_value ) -> str:
        num_levels = len( key_chain )
        assert( num_levels > 0 )
        
        # Drill down into the settings along the designated branch.
        setting_section = self.settings
        for key in key_chain:
            try:
                setting_section = setting_section[ key ]
            except KeyError:
                # This key is not yet in the settings, add it.
                if ( num_levels > 1 ):
                    setting_section[ key ] = {}
                else:
                    setting_section[ key ] = str( default_value )
                self.are_settings_dirty = True
                setting_section = setting_section[ key ]
            num_levels -= 1

        value = str( default_value )
        try:
            value = str( setting_section )
        except:
            print( f"WARN: Unable to convert {setting_section} to string. Using default of {value} instead." )
            pass
            
        return value

    # Update a setting.
    #
    # Preconditions:
    # self.settings is a dictionary which has been populated.
    #
    # Invariants:
    # No settings outside the key_chain entry, are modified during this call.
    #
    # Postconditions:
    # The value is stored as a string at the branch indexed by key_chain.
    def set_value( self, key_chain: list, new_value ) -> None:
        assert( len( key_chain ) > 0 )
        
        # Drill down into the settings along the designated branch.
        setting_section = self.settings
        for key in key_chain[ : -1 ]:
            try:
                setting_section = setting_section[ key ]
            except KeyError:
                # This key is not yet in the settings, add it.
                setting_section[ key ] = {}
                self.are_settings_dirty = True
                setting_section = setting_section[ key ]

        if setting_section[ key_chain[ -1 ] ] != str( new_value ):
            setting_section[ key_chain[ -1 ] ] = str( new_value )
            self.are_settings_dirty = True
            #print( f"Set: keys = {key_chain}, new_val = {new_value}" )

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
        # Retrieve from current settings.
        width_str = self.get_value( [ "app_window", "width" ], self.default_width )
        
        # This form allows for alternate number bases (i.e. hex strings).
        width = int( width_str, 0 )
        
        # Validate the retrieved width.
        if ( width <= 0 or width > self.max_width ):
            width = self.default_width
        
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
    def set_app_width( self, width: int = None ) -> None:
        if width is None:
            width = self.default_width

        if ( width <= 0 or width >= self.max_width ):
            # Invalid width, can't use it.
            
            # See what is already in the settings.
            curr_width = self.get_app_width()
            
            # Validate what was in settings.
            if ( curr_width > 0 and curr_width <= self.max_width ):
                width = curr_width
            else:
                width = self.default_width

        self.set_value( [ "app_window", "width" ], width )

    # If the current setting is valid, return that. If not:
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
        # Retrieve from current settings.
        height_str = self.get_value( [ "app_window", "height" ], self.default_height )
        
        # This form allows for alternate number bases (i.e. hex strings).
        height = int( height_str, 0 )
        
        # Validate the retrieved height.
        if ( height <= 0 or height > self.max_height ):
            height = self.default_height
        
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
    def set_app_height( self, height: int = None ) -> None:
        if height is None:
            height = self.default_height

        if ( height <= 0 or height >= self.max_height ):
            # Invalid height, can't use it.
            
            # See what is already in the settings.
            curr_height = self.get_app_height()
            
            # Validate what was in settings.
            if ( curr_height > 0 and curr_height <= self.max_height ):
                height = curr_height
            else:
                height = self.default_height

        self.set_value( [ "app_window", "height" ], height )

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
    def set_app_size( self, width: int = None, height: int = None ) -> None:
        # Resolve valid application window size.
        self.set_app_width( width )
        self.set_app_height( height )

    # Read the application window's left position ( x ) from current settings.
    # If valid, return that. If not:
    #   Set the left to a fixed default.
    #
    # Preconditions:
    # self.settings is a dictionary which has been populated.
    #
    # Invariants:
    # No settings outside the "app_window" section are modified during this call.
    #
    # Postconditions:
    # left in the settings data is set to a valid position for the display.
    #
    # Returns:
    # A valid left position for the display.
    def get_app_left( self ) -> int:
        # Retrieve from current settings.
        left_str = self.get_value( [ "app_window", "left" ], DEFAULT_APP_LEFT )

        # This form allows for alternate number bases (i.e. hex strings).
        left = int( left_str, 0 )

        # Validate the retrieved left.
        if ( left < 0 or left > self.max_width ):
            left = DEFAULT_APP_LEFT

        return left
        

    # Set the application window's left position ( x ) into current settings.
    # If valid, new value is stored.
    #
    # Preconditions:
    # self.settings is a dictionary which has been populated.
    #
    # Invariants:
    # No settings outside the "app_window" section are modified during this call.
    #
    # Postconditions:
    # left in the settings data is set to a valid left position for the display.
    def set_app_left( self, left: int = None ) -> None:
        if left is None:
            left = DEFAULT_APP_LEFT

        if ( left < 0 or left >= self.max_width ):
            # Invalid left position, don't set it.
            # Use what is already in the settings.
            left = self.get_app_left()

        self.set_value( [ "app_window", "left" ], left )

    # Read the application window's top position ( y ) from current settings.
    # If valid, return that. If not:
    #   Set the top to a fixed default.
    #
    # Preconditions:
    # self.settings is a dictionary which has been populated.
    #
    # Invariants:
    # No settings outside the "app_window" section are modified during this call.
    #
    # Postconditions:
    # top in the settings data is set to a valid position for the display.
    #
    # Returns:
    # A valid top position for the display.
    def get_app_top( self ) -> int:
        # Retrieve from current settings.
        top_str = self.get_value( [ "app_window", "top" ], DEFAULT_APP_TOP )

        # This form allows for alternate number bases (i.e. hex strings).
        top = int( top_str, 0 )

        # Validate the retrieved top.
        if ( top < 0 or top > self.max_height ):
            top = DEFAULT_APP_TOP

        return top

    # Set the application window's top position ( y ) into current settings.
    # If valid, new value is stored.
    #
    # Preconditions:
    # self.settings is a dictionary which has been populated.
    #
    # Invariants:
    # No settings outside the "app_window" section are modified during this call.
    #
    # Postconditions:
    # top in the settings data is set to a valid top position for the display.
    def set_app_top( self, top: int = None ) -> None:
        if top is None:
            top = DEFAULT_APP_TOP

        if ( top < 0 or top >= self.max_height ):
            # Invalid top position, don't set it.
            # Use what is already in the settings.
            top = self.get_app_top()

        self.set_value( [ "app_window", "top" ], top )

    # Retrieve window position from settings.
    #
    # Preconditions:
    # None.
    #
    # Invariants:
    # No other settings are modified during this call.
    #
    # Postconditions:
    # left and top are internally set to valid values for the display monitor on which
    # the app was launched.
    #
    # Returns:
    # A tuple containing ( left, top ) pixel coordinates of the application window.
    def get_app_posn( self ) -> tuple:
        left = self.get_app_left()
        top = self.get_app_top()
        return ( left, top )

    # Confirm the requested left and top are valid for the display. If valid update the
    # setting(s). If either is invalid, first check the current setting and if valid just
    # keep it. If current and requested are both invalid, set to a fixed default value.
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
    def set_app_posn( self, left: int = None, top: int = None ) -> None:
        set_app_left( left )
        set_app_top( top )


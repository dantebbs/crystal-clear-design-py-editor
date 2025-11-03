####################################################################################################
# Manage the settings which the user wants to keep across development sessions using a JSON data
# file. Default settings are used if either the file or the field is not available.
####################################################################################################

import inspect
import io
import os
import json
import mru
import hsm_defaults


# Workspace-specific defaults.
DEFAULT_WS_FILENAME = "workspace.json"
DEFAULT_APP_LEFT = 200
DEFAULT_APP_TOP = 100
DEFAULT_APP_WIN = f"""{{
    "left": {DEFAULT_APP_LEFT},
    "top": {DEFAULT_APP_TOP},
    "width": 0,
    "height": 0
  }}"""
DEFAULT_JSON = f"""{{
  "app_window": {DEFAULT_APP_WIN},
  "mru_models": [ "hsm_model.json" ],
  "settings": {{"autosave": 1}}
}}
"""
# Default to an arbitrary fraction of width and height of the current monitor if invalid.
DEFAULT_DISPLAY_PERCENT = 60

# An arbitrary length for the max number of recently used models to track.
DEFAULT_MAX_MRU_MODELS = 50


# Multiple weights might be added later.
#BRD_WEIGHT_THN = 0
#BRD_WEIGHT_MED = 1
#BRD_WEIGHT_THK = 2


class workspace_settings_cl:
    def __init__( self ) -> None:
        return

    def create_default_settings( self ) -> None:
        # Reset the filename to ensure a valid default.
        print( f"INFO: Creating default workspace file {self.settings_filename}." )
        self.settings_filename = DEFAULT_WS_FILENAME
        self.are_settings_dirty = True

        try:
            self.settings = json.loads( DEFAULT_JSON )
        except json.JSONDecodeError as e:
            print( f"ERR: JSONDecodeError, {e.msg}, str=\"{DEFAULT_JSON}\", line = {e.lineno}, col = {e.colno}." )
            exit()

        self.sync_to_disk()
    
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
    def get_value( self, key_chain: list, default_value: str ) -> str:
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
            value = setting_section
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
        assert( type( key_chain ) == list )
        
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

        if setting_section[ key_chain[ -1 ] ] != new_value:
            setting_section[ key_chain[ -1 ] ] = new_value
            self.are_settings_dirty = True
            #print( f"Set: keys = {key_chain}, new_val = {new_value}, type = {type( new_value )}" )

####################################################################################################
curr_settings = workspace_settings_cl()
#dir( curr_settings )

####################################################################################################
def load_settings( screen_max_x: int, screen_max_y: int, filename: str = DEFAULT_WS_FILENAME ) -> None:
    # Select reasonable defaults for when attempted values are invalid.
    curr_settings.max_width = screen_max_x
    curr_settings.default_width  = int( curr_settings.max_width * DEFAULT_DISPLAY_PERCENT / 100 )
    curr_settings.max_height = screen_max_y
    curr_settings.default_height = int( curr_settings.max_height * DEFAULT_DISPLAY_PERCENT / 100 )

    # Put a minimal default set in place.
    try:
        curr_settings.settings = json.loads( DEFAULT_JSON )
    except json.JSONDecodeError as e:
        print( f"ERR: JSONDecodeError, {e.msg}, str=\"{DEFAULT_JSON}\", line = {e.lineno}, col = {e.colno}." )
        exit()

    # See if the workspace file exists in the current folder.
    curr_settings.settings_filename = filename
    if not os.path.isfile( filename ):
        # File isn't here, create a default workspace in the current folder.
        print( f"WARN: File {filename} not found when loading workspace file." )
        curr_settings.create_default_settings()
    
    # Deserialize the JSON settings.
    try:
        print( f"INFO: Loading workspace file \"{curr_settings.settings_filename}\"." )

        sess_file = open( curr_settings.settings_filename, "r" )
        if not sess_file:
            print( f"WARN: There is something wrong with the file {curr_settings.settings_filename}, and it can't be opened." )
            print( f"WARN: Try deleting the file (or renaming it), and starting with fresh settings." )
            print( f"WARN: Continuing with default settings." )
            return

        # Make sure it isn't empty.
        sess_file_len = os.fstat(sess_file.fileno()).st_size
        if sess_file_len > 0:
            try:
                curr_settings.settings = json.load( sess_file )
            except json.JSONDecodeError as e:
                print( f"ERR: JSONDecodeError, {e.msg}, file=\"{curr_settings.settings_filename}\", line = {e.lineno}, col = {e.colno}." )
                curr_settings.create_default_settings()
            
        sess_file.close()
    except FileNotFoundError:
        curr_settings.create_default_settings()

    curr_settings.are_settings_dirty = False
    #print( f'wid = {curr_settings.settings[ "app_window" ][ "width"  ]}, hgt = {curr_settings.settings[ "app_window" ][ "height"  ]}' )

    mru_models = curr_settings.get_value( [ "mru_models" ], [] )
    curr_settings.mru_models = mru.mru( mru_models, DEFAULT_MAX_MRU_MODELS )
    
    #curr_settings.layout_style_weight = curr_settings.get_value( "layout_style_weight", BRD_WEIGHT_THN )

    return

####################################################################################################
# Write any settings changes to disk.
def sync_to_disk() -> None:
    if curr_settings.are_settings_dirty:
        mru_list = curr_settings.mru_models.get_list()
        curr_settings.set_value( [ "mru_models" ], mru_list )
        #print( f"INFO: Updating \"{curr_settings.settings_filename}\" to {curr_settings.settings}" )
        sess_file = open( curr_settings.settings_filename, "w" )
        json.dump( curr_settings.settings, sess_file, ensure_ascii = True, indent = 4 )
        sess_file.close()
        curr_settings.are_settings_dirty = False

####################################################################################################
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
def get_app_width() -> int:
    # Retrieve from current settings.
    width = curr_settings.get_value( [ "app_window", "width" ], curr_settings.default_width )
    
    # Validate the retrieved width.
    if ( width <= 0 or width > curr_settings.max_width ):
        width = curr_settings.default_width
    
    return width

####################################################################################################
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
def set_app_width( width: int = None ) -> None:
    if width is None:
        width = curr_settings.default_width

    if ( width <= 0 or width >= curr_settings.max_width ):
        # Invalid width, can't use it.
        
        # See what is already in the settings.
        curr_width = curr_settings.get_app_width()
        
        # Validate what was in settings.
        if ( curr_width > 0 and curr_width <= curr_settings.max_width ):
            width = curr_width
        else:
            width = curr_settings.default_width

    curr_settings.set_value( [ "app_window", "width" ], width )

####################################################################################################
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
def get_app_height() -> int:
    # Retrieve from current settings.
    height = curr_settings.get_value( [ "app_window", "height" ], curr_settings.default_height )

    # Validate the retrieved height.
    if ( height <= 0 or height > curr_settings.max_height ):
        height = curr_settings.default_height
    
    return height

####################################################################################################
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
def set_app_height( height: int = None ) -> None:
    if height is None:
        height = curr_settings.default_height

    if ( height <= 0 or height >= curr_settings.max_height ):
        # Invalid height, can't use it.
        
        # See what is already in the settings.
        curr_height = curr_settings.get_app_height()
        
        # Validate what was in settings.
        if ( curr_height > 0 and curr_height <= curr_settings.max_height ):
            height = curr_height
        else:
            height = curr_settings.default_height

    curr_settings.set_value( [ "app_window", "height" ], height )

####################################################################################################
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
def get_app_size() -> tuple:
    width = get_app_width()
    height = get_app_height()
    return ( width, height )

####################################################################################################
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
def set_app_size( width: int = None, height: int = None ) -> None:
    # Resolve valid application window size.
    set_app_width( width )
    set_app_height( height )

####################################################################################################
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
def get_app_left() -> int:
    # Retrieve from current settings.
    left = curr_settings.get_value( [ "app_window", "left" ], DEFAULT_APP_LEFT )

    # Validate the retrieved left.
    if ( left < 0 or left > curr_settings.max_width ):
        left = DEFAULT_APP_LEFT

    return left
    

####################################################################################################
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
def set_app_left( left: int = None ) -> None:
    if left is None:
        left = DEFAULT_APP_LEFT

    if ( left < 0 or left >= curr_settings.max_width ):
        # Invalid left position, don't set it.
        # Use what is already in the settings.
        left = curr_settings.get_app_left()

    curr_settings.set_value( [ "app_window", "left" ], left )

####################################################################################################
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
def get_app_top() -> int:
    # Retrieve from current settings.
    top = curr_settings.get_value( [ "app_window", "top" ], DEFAULT_APP_TOP )

    # Validate the retrieved top.
    if ( top < 0 or top > curr_settings.max_height ):
        top = DEFAULT_APP_TOP

    return top

####################################################################################################
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
def set_app_top( top: int = None ) -> None:
    if top is None:
        top = DEFAULT_APP_TOP

    if ( top < 0 or top >= curr_settings.max_height ):
        # Invalid top position, don't set it.
        # Use what is already in the settings.
        top = curr_settings.get_app_top()

    curr_settings.set_value( [ "app_window", "top" ], top )

####################################################################################################
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
def get_app_posn() -> tuple:
    left = get_app_left()
    top = get_app_top()
    return ( left, top )

####################################################################################################
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
def set_app_posn( left: int = None, top: int = None ) -> None:
    curr_settings.set_app_left( left )
    curr_settings.set_app_top( top )

####################################################################################################
# See if an MRU file path is available.
# If not, will return None.
def get_latest_used_model() -> str:
    return curr_settings.mru_models.get_at_idx()

# Indicate that a model file has been opened for editing, making it the MRU file.
#
# Preconditions:
# None
#
# Invariants:
# Only the self.mru_models member variable is modified. All other settings remain.
#
# Postconditions:
# If the MRU list is maxed out, the oldest (now least recently used) item is dropped.
#
# Param:  latest  This is a path and filename, valid for the host platform.
def set_latest_used_model( latest: str ) -> None:
    curr_settings.mru_models.touch( latest )
    curr_settings.are_settings_dirty = True

####################################################################################################
## Perhaps add support for different border weights later on.
#def set_border_thickness( weight_idx: int ):
#    print( f"weight_idx = {weight_idx}" )
#    print( f"type( weight_idx ) = {type( weight_idx ) is int}" )
#    assert( type( weight_idx ) is int and
#          ( weight_idx == workspace_settings.BRD_WEIGHT_THN
#         or weight_idx == workspace_settings.BRD_WEIGHT_MED
#         or weight_idx == workspace_settings.BRD_WEIGHT_THK ) )
#    curr_settings.border_weight_idx = weight_idx
#
#def get_border_thickness():
#    return curr_settings.border_weight_idx
#

####################################################################################################
# Read the application's autosave flag from current settings.
# If valid, return that. If not:
#   Set the autosave to a fixed default.
#
# Preconditions:
# self.settings is a dictionary which has been populated.
#
# Invariants:
# No settings outside the "autosave" section are modified during this call.
#
# Postconditions:
# autosave in the settings data is set to a valid position for the application.
#
# Returns:
# The autosave flag for the application.
def get_autosave() -> int:
    # Retrieve from current settings.
    autosave = curr_settings.get_value( [ "settings", "autosave" ], True )

    # Validate the retrieved top.
    if ( autosave < 0 or autosave > curr_settings.max_height ):
        autosave = True

    return autosave

####################################################################################################
# Set the autosave flag into current settings.
#
# Preconditions:
# self.settings is a dictionary which has been populated.
#
# Invariants:
# No settings outside the "app_window" section are modified during this call.
#
# Postconditions:
# top in the settings data is set to a valid top position for the display.
def set_autosave( top: int = None ) -> None:
    if top is None:
        top = DEFAULT_APP_TOP

    if ( top < 0 or top >= curr_settings.max_height ):
        # Invalid top position, don't set it.
        # Use what is already in the settings.
        top = curr_settings.get_app_top()

    curr_settings.set_value( [ "app_window", "top" ], top )


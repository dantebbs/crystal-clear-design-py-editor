import json
import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import *
import workspace_settings
import hsm_defaults


HSM_BLANK_TEMPLATE = """
{
  "events": [
    "timeout_1000ms"
  ],
  "states": {
    "start": {
      "tran": {
        "auto": {
          "dest": "stop"
        }
      }
    },
    "stop": {
    }
  }
}
"""
HSM_DEFAULT_FILENAME = "hsm_model.json"

HSM_TEST_01 = """
{
  "events": [
    "timeout_1000ms"
  ],
  "states": {
    "start": {
      "tran": {
        "auto": {
          "dest": "Counting Seconds"
        }
      }
    },
    "Counting Seconds": {
      "entry": [
        "update_display(seconds_counted)"
      ],
      "tran": {
        "timeout_1000ms": {
          "dest": "Counting Seconds"
        }
      }
    }
  }
}
"""


# Get the name of this particular code module.
this_module = sys.modules[__name__]

####################################################################################################
class ccd_model_cl( dict ):
    def __init__( self, *args ):
        dict.__init__( self, *args )

        # A flag showing that one or more changes has been made,
        # and the model needs to be saved to file again.
        self.has_model_changed = False
        self.filename = ""

        # Provide a default blank model until the model is loaded from a file.
        try:
            self = json.loads( HSM_BLANK_TEMPLATE )
        except json.JSONDecodeError as e:
            print( f"ERR: JSONDecodeError, {e.msg}, file=\"{HSM_BLANK_TEMPLATE}\", line = {e.lineno}, col = {e.colno}." )

    def __getitem__( self, key ):
        val = dict.__getitem__( self, key )
        #log.info("GET %s['%s'] = %s" % str(dict.get(self, 'name_label')), str(key), str(val)))
        return val

    def __setitem__( self, key, val ):
        #log.info("SET %s['%s'] = %s" % str(dict.get(self, 'name_label')), str(key), str(val)))
        if ( key not in self.keys() ):
            self.has_model_changed = True
        elif ( val != self[ key ] ):
            self.has_model_changed = True
        dict.__setitem__( self, key, val )

####################################################################################################
global curr_model
curr_model = ccd_model_cl( {} )

####################################################################################################
def get_sub_states( state: dict ) -> dict:
    print( f"get_sub_states( state: {type( state )} )" )
    assert( isinstance( state, dict ) )
    return state.get( hsm_defaults.RSVD_STATES )

####################################################################################################
def get_state_layout( state: dict, default_outline: dict = hsm_defaults.SM_OUTLINE_DEF ) -> dict:
    layout = state.get( hsm_defaults.RSVD_LYOUT, default_outline )
    #print( f"State \"{state}\" has layout {layout}." )
    return layout

####################################################################################################
def get_trans_layout( trans: dict ) -> dict:
    return trans.get( hsm_defaults.RSVD_LYOUT )

####################################################################################################
def get_transitions( state:dict ) -> list:
    transition_list = []
    states = state.get( hsm_defaults.RSVD_STATES, {} )
    if states:
        for state_name, sub_state in states.items():
            if sub_state.get( hsm_defaults.RSVD_TRAN ):
                transitions = dict( sub_state.get( hsm_defaults.RSVD_TRAN ) )
                for transition_name, transition in transitions.items():
                    transition[ hsm_defaults.RSVD_SRC ] = state_name
                    transition[ hsm_defaults.RSVD_DEST ] = transition_name
                    transition_list.append( transition )
            sub_state_trans = get_transitions( state )
            transition_list.append( sub_state_trans )
    return transition_list

####################################################################################################
def set_position( state: dict, x: int, y: int ):
    assert( type( state ) is dict )
    assert( type( x ) is int )
    assert( type( y ) is int )
    state[ hsm_defaults.RSVD_LYOUT ][ hsm_defaults.RSVD_LFT ] = x
    state[ hsm_defaults.RSVD_LYOUT ][ hsm_defaults.RSVD_TOP ] = y
    ccd_model.has_model_changed = True

####################################################################################################
def find_paint_rect( state: dict, min_x: int, min_y:int, max_x: int, max_y: int ) -> tuple:
    # Push extents out as needed to cover the state outline.
    layout = state.get( hsm_defaults.RSVD_LYOUT )
    if layout:
        x1 = layout.get( hsm_defaults.RSVD_LFT, min_x )
        if min_x > x1:
            min_x = x1
        y1 = layout.get( hsm_defaults.RSVD_TOP, min_y )
        if min_y > y1:
            min_y = y1
        x2 = x1 + layout.get( hsm_defaults.RSVD_WID, hsm_defaults.SM_OUTLINE_DEF[ hsm_defaults.RSVD_WID ] )
        if max_x < x2:
            max_x = x2
        y2 = y1 + layout.get( hsm_defaults.RSVD_HGT, hsm_defaults.SM_OUTLINE_DEF[ hsm_defaults.RSVD_HGT ] )
        if max_y < y2:
            max_y = y2
    else:
        if  max_x < min_x + hsm_defaults.SM_OUTLINE_DEF[ hsm_defaults.RSVD_WID ]:
            max_x = min_x + hsm_defaults.SM_OUTLINE_DEF[ hsm_defaults.RSVD_WID ]
        if  max_y < min_y + hsm_defaults.SM_OUTLINE_DEF[ hsm_defaults.RSVD_HGT ]:
            max_y = min_y + hsm_defaults.SM_OUTLINE_DEF[ hsm_defaults.RSVD_HGT ]

    sub_states = get_sub_states( state )
    if sub_states:
        transitions = dict( sub_states.get( hsm_defaults.RSVD_TRAN ) )
        for transition_name, transition in transitions.items():
            # Push extents out again as needed to cover each transition path.
            path = transition.get( hsm_defaults.RSVD_PATH )
            if path:
                for point in path:
                    x = point.get( hsm_defaults.RSVD_LFT )
                    if not None:
                        if min_x > x:
                            min_x = x
                        if max_x < x:
                            max_x = x
                    y = point.get( hsm_defaults.RSVD_TOP )
                    if not None:
                        if min_y > y:
                            min_y = y
                        if max_y < y:
                            max_y = y

        # Recursion to account for sub-states.
        for state_name, sub_state in sub_states.items():
            ( min_x, min_y, max_x, max_y ) = find_paint_rect( sub_state, min_x, min_y, max_x, max_y )

    return ( min_x, min_y, max_x, max_y )


####################################################################################################
def load_model_from_file( filename: str = "" ):
    # See if the file exists as listed.
    if not os.path.isfile( filename ):
        # File isn't there, can't load it.
        print( f"WARN: File \"{filename}\" not found when loading state machine model file." )
    else:
        # Deserialize the JSON state machine description.
        try:
            print( f"INFO: Loading project file \"{filename}\"." )
            model_file = open( filename, "r" )
            if not model_file:
                print( f"WARN: There is something wrong with the file {filename}, and it can't be opened." )
            else:
                try:
                    curr_model = ccd_model_cl( json.load( model_file ) )
                    curr_model.filename = filename
                    curr_model.has_model_changed = False
                    workspace_settings.set_latest_used_model( filename )
                except json.JSONDecodeError as e:
                    print( f"ERR: JSONDecodeError, {e.msg}, file=\"{filename}\", line = {e.lineno}, col = {e.colno}." )

                model_file.close()
        except OSError:
            print( f"WARN: There is something wrong with the file {filename}, and it can't be opened." )
            
    return

####################################################################################################
def save_model_to_file( tk_canvas: object, filename: str = "" ) -> bool:
    if ( ( filename == "" or filename == curr_model.filename ) and not curr_model.has_model_changed ):
        # This is a request to save the current model, but there are no changes to save.
        return True

    result = False
    use_dialog = True
    # When the autosave setting is selected, in some cases we can skip the dialog.
    should_auto_save = workspace_settings.get_autosave()
    #get_value( [ "settings", "autosave" ], False )

    # If no filename is supplied, assume the request is to save the current file.
    filename_to_save = filename
    if ( filename_to_save == "" ):
        filename_to_save = self.filename
        if ( should_auto_save ):
            use_dialog = False
    
    # If no filename was supplied earlier, supply a default name and a dialog box.
    if ( filename_to_save == "" ):
        filename_to_save = HSM_DEFAULT_FILENAME

    # Serialize the JSON state machine description.
    try:
        if ( use_dialog ):
            filename_to_save = filedialog.asksaveasfilename( parent = tk_canvas,
              title = "Select Save File Name",
              initialdir = ".",
              initialfile = filename_to_save,
              filetypes = ( ( "JSON files","*.json" ), ( "all files","*.*" ) ),
              defaultextension = "json",
              confirmoverwrite = False )
        model_file = open( filename_to_save, "w" )
        workspace_settings.set_latest_used_model( filename_to_save )
        json.dump( curr_model, model_file, ensure_ascii = True, indent = 4 )
        model_file.close()
        curr_model.has_model_changed = False
        result = True
    
        print( f"INFO: Saved model to file \"{filename_to_save}\"." )
    except OSError:
        print( f"WARN: There is something wrong with the file {filename_to_save}, and it can't be opened for writing." )
        
    return result

####################################################################################################
def set_state_size( state: dict, wid: int, hgt: int ):
    assert( state )
    state.model[ hsm_defaults.RSVD_LYOUT ][ hsm_defaults.RSVD_WID ] = wid
    state.model[ hsm_defaults.RSVD_LYOUT ][ hsm_defaults.RSVD_HGT ] = hgt



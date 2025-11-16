import json
import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import *
import workspace_settings
import hsm_defaults


# Get the name of this particular code module.
this_module = sys.modules[__name__]


# Use this when you want to access all states in the model.
# i.e. top_level_states = get_sub_states( ROOT_PATH )
ROOT_PATH = []


# TODO: Delete this example when done.
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

# TODO: Create a set of regression tests.
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


####################################################################################################
# Returns True only if:
#   - It is of type list
#   - There are exactly 2 elements
#   - Each element is of type int
def is_valid_2d_point( point_to_check: list ) -> bool:
    if ( not isinstance( point_to_check, list ) ):
        assert( not "point is not in the form of a list." )
        return False

    if ( len( point_to_check ) != 2 ):
        assert( not "point is not 2D." )
        return False

    if ( not isinstance( point_to_check[ 0 ], int ) ):
        assert( not "point's 1st element (x) is of type {type( point_to_check[ 0 ])}, must be of type int." )
        return False

    if ( not isinstance( point_to_check[ 1 ], int ) ):
        assert( not "point's 2nd element (y) is of type {type( point_to_check[ 1 ])}, must be of type int." )
        return False
    
    return True

####################################################################################################
# A feature is included where state names are allowed to be reused.
# This neccessitates disambiguation by using a full path for each state reference.
# Getting and setting properties of a state use this full path for indexing.
# Note: This is different from the layout paths, which contain x and y points. This path represents
# the hierarchical tree of states with parent-child relationships.
class ccd_state_path( list[ str ] ):
    def __init__( self, *args ):
        list.__init__( self, *args )


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
    
    def get_state_reference( self, state_path: ccd_state_path ) -> dict:
        assert( isinstance( state_path, ccd_state_path )
           or ( isinstance( state_path, list ) ) )
        for state in state_path:
            assert( isinstance( state, str ) )
        
        state_reference = self
        for state_path_idx in range( len( state_path ) ):
            sub_states = state_reference.get( hsm_defaults.RSVD_STATES )
            assert( state_path[ state_path_idx ] in sub_states )
            state_reference = sub_states.get( state_path[ state_path_idx ] )
        
        return state_reference
        
    def get_substate_paths( self, state_path: ccd_state_path ) -> list[ ccd_state_path ]:
        assert( isinstance( state_path, ccd_state_path )
           or ( isinstance( state_path, list ) ) )
        for state in state_path:
            assert( isinstance( state, str ) )
        
        state = self.get_state_reference( state_path )
        sub_state_paths = []
        sub_states = state.get( hsm_defaults.RSVD_STATES )
        for sub_state_name, sub_state in sub_states.items():
            sub_state_path = state_path[:]
            sub_state_path.append( sub_state_name )
            sub_state_paths.append( sub_state_path )
        #print( f'sub_states = {sub_state_paths}' )

####################################################################################################
curr_model = ccd_model_cl( {} )

####################################################################################################
def get_tree_path( state: dict ) -> list:
    assert( isinstance( state, dict ) )
    tree_path = state.get( hsm_defaults.RSVD_TREE_PATH, [] )
    
    assert( isinstance( tree_path, list ) )
    return tree_path


####################################################################################################
def get_sub_states( state: dict ) -> dict:
    assert( isinstance( state, dict ) )
    return state.get( hsm_defaults.RSVD_STATES )

####################################################################################################
# Returns: A 4-tuple of the form ( x1, y1, x2, y2 ) or ( left, top, right, bottom )
def get_state_layout( state: dict, default_outline: dict = hsm_defaults.SM_OUTLINE_DEF ) -> tuple:
    assert( isinstance( state, dict ) )
    assert( isinstance( default_outline, dict ) )
    layout = state.get( hsm_defaults.RSVD_LYOUT, default_outline )
    #print( f"State \"{state}\" has layout {layout}." )
    return ( layout[ hsm_defaults.RSVD_LFT ],
             layout[ hsm_defaults.RSVD_TOP ],
             layout[ hsm_defaults.RSVD_RGT ],
             layout[ hsm_defaults.RSVD_BOT ] )

####################################################################################################
def set_state_layout( state: dict, new_layout: tuple ) -> None:
    assert( isinstance( state, dict ) )
    assert( len( state ) > 0 )
    assert( isinstance( new_layout, tuple ) )
    assert( len( new_layout ) == 4 )
    
    layout = state.get( hsm_defaults.RSVD_LYOUT, new_layout )
    #print( f"Changing State \"{state}\" to new layout {layout}." )
    layout[ hsm_defaults.RSVD_LFT ] = new_layout[ 0 ]
    layout[ hsm_defaults.RSVD_TOP ] = new_layout[ 1 ]
    layout[ hsm_defaults.RSVD_RGT ] = new_layout[ 2 ]
    layout[ hsm_defaults.RSVD_BOT ] = new_layout[ 3 ]
    curr_model.has_model_changed = True

####################################################################################################
def get_trans_layout( trans: dict ) -> dict:
    assert( isinstance( trans, dict ) )
    return trans.get( hsm_defaults.RSVD_TRAN_PATH )

####################################################################################################
def get_transitions( state: dict ) -> list:
    assert( isinstance( state, dict ) )
    return state.get( hsm_defaults.RSVD_TRAN, [] )

####################################################################################################
# Returns a list of lists (points) of length 2+ holding the beginning and ending points, and any
# additional intermediate points, of the form [ [ x0, y0 ], [ x1, y1 ], ... [ xN-1, yN-1 ] ].
def get_transition_path( transition: dict ) -> list:
    assert( isinstance( transition, dict ) )
    
    #condition = list( transition.keys() )[ 0 ]
    #transition_fields = transition[ condition ]
    #print( f'transition_fields = {json.dumps( transition_fields, indent = 2 )}' )
    #layout_path = transition_fields.get( hsm_defaults.RSVD_TRAN_PATH, {} )
    layout_path = transition.get( hsm_defaults.RSVD_TRAN_PATH, [] )

    return layout_path

####################################################################################################
def get_path_point( transition: dict, point_index: int ) -> list:
    assert( isinstance( transition, dict ) )
    assert( isinstance( point_index, int ) )

    path = transition.get( hsm_defaults.RSVD_TRAN_PATH )
    assert( ( point_index >= -len( path ) )
        and ( point_index < len( path ) ) )
    transition_path_point = path[ point_index ]

    if ( not is_valid_2d_point( transition_path_point ) ):
        return []

    return transition_path_point

####################################################################################################
def set_path_point( transition: dict, point_index: int, new_point: list ) -> bool:
    assert( isinstance( transition, dict ) )
    assert( isinstance( point_index, int ) )

    path = transition.get( hsm_defaults.RSVD_TRAN_PATH )
    assert( ( point_index >= -len( path ) )
        and ( point_index < len( path ) ) )

    if ( not is_valid_2d_point( new_point ) ):
        return False

    transition[ hsm_defaults.RSVD_TRAN_PATH ][ point_index ] = new_point
    curr_model.has_model_changed = True
    return True

####################################################################################################
# Returns a tree_path (list of strs) of length 1+ holding the beginning state for the transition.
def get_transition_src( transition: dict ) -> list:
    assert( isinstance( transition, dict ) )
    
    src_path = transition.get( hsm_defaults.RSVD_SRC, [] )

    assert( isinstance( src_path, list ) )
    return src_path

####################################################################################################
# Returns a tree_path (list of strs) of length 1+ holding the ending state for the transition.
def get_transition_dest( transition: dict ) -> list:
    assert( isinstance( transition, dict ) )
    
    dest_path = transition.get( hsm_defaults.RSVD_DEST, [] )

    assert( isinstance( dest_path, list ) )
    return dest_path

####################################################################################################
def set_position( state: dict, x: int, y: int ):
    assert( type( state ) is dict )
    assert( type( x ) is int )
    assert( type( y ) is int )
    state[ hsm_defaults.RSVD_LYOUT ][ hsm_defaults.RSVD_LFT ] = x
    state[ hsm_defaults.RSVD_LYOUT ][ hsm_defaults.RSVD_TOP ] = y
    curr_model.has_model_changed = True

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
        x2 = layout.get( hsm_defaults.RSVD_RGT, hsm_defaults.SM_OUTLINE_DEF[ hsm_defaults.RSVD_RGT ] )
        if max_x < x2:
            max_x = x2
        y2 = layout.get( hsm_defaults.RSVD_BOT, hsm_defaults.SM_OUTLINE_DEF[ hsm_defaults.RSVD_BOT ] )
        if max_y < y2:
            max_y = y2
    else:
        if  max_x < hsm_defaults.SM_OUTLINE_DEF[ hsm_defaults.RSVD_RGT ]:
            max_x = hsm_defaults.SM_OUTLINE_DEF[ hsm_defaults.RSVD_RGT ]
        if  max_y < hsm_defaults.SM_OUTLINE_DEF[ hsm_defaults.RSVD_BOT ]:
            max_y = hsm_defaults.SM_OUTLINE_DEF[ hsm_defaults.RSVD_BOT ]

    sub_states = get_sub_states( state )
    if sub_states:
        #transitions = dict( sub_states.get( hsm_defaults.RSVD_TRAN ) )
        transitions = get_transitions( state )
        if transitions:
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
                    global curr_model
                    curr_model = ccd_model_cl( json.load( model_file ) )
                    #print( f"Inp model:" )
                    #print( json.dumps( curr_model, indent = 2 ) )
                    curr_model.filename = filename
                    curr_model.has_model_changed = False
                    workspace_settings.set_latest_used_model( filename )
                except json.JSONDecodeError as e:
                    print( f"ERR: JSONDecodeError, {e.msg}, file=\"{filename}\", line = {e.lineno}, col = {e.colno}." )

                model_file.close()
        except OSError:
            print( f"WARN: There is something wrong with the file {filename}, and it can't be opened." )
            
    #print( f'INFO: Loaded {curr_model}' )
    return

####################################################################################################
def save_model_to_file( tk_canvas: object, filename: str = "" ) -> bool:
    global curr_model
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
        filename_to_save = curr_model.filename
        if ( should_auto_save ):
            use_dialog = False
    
    # If no filename was supplied earlier, supply a default name and a dialog box.
    if ( filename_to_save == "" ):
        filename_to_save = hsm_defaults.HSM_DEFAULT_FILENAME

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

####################################################################################################
# Returns True if both lists have the same sequence of identical strings.
def compare_tree_paths( lft_state_path: list, rgt_state_path: list ) -> bool:
    assert( isinstance( lft_state_path, list ) )
    assert( isinstance( rgt_state_path, list ) )
    
    if lft_state_path == rgt_state_path:
        # 2 references to the same object, no need to continue.
        return True
    if len( lft_state_path ) != len( rgt_state_path ):
        # The 2 lists have to contain the same number of strings.
        return False

    for path_level_idx in range( len( lft_state_path ) ):
        lft_state_name = lft_state_path[ path_level_idx ]
        assert( isinstance( lft_state_name, str ) )
        rgt_state_name = rgt_state_path[ path_level_idx ]
        assert( isinstance( rgt_state_name, str ) )
        
        if lft_state_name != rgt_state_name:
            # Found a disparity, the 2 lists are not equal.
            return False

    # Made it through the full tree path and matched the state name at each level.
    return True
        

####################################################################################################
# Gives the full list of transitions currently in the model for the supplied state and all of its
# sub-states.
# Does a depth-first tree traversal to visit each sub-state.
# Note: Maxes out at 20 levels (0 through 19).
# Returns copies of the dict entries describing the transition, with a reference to the source state
# added under the index RSVD_SRC.
def get_transitions_recurse( state: dict ) -> list:
    assert( isinstance( state, dict ) )

    # Start the list with the transitions exiting this state.
    transitions_list = get_transitions( state )
    #print( f'385 transitions_list = {json.dumps( transitions_list, indent = 2 )}' )
    
    # Iterate any sub-states.
    sub_states = get_sub_states( state )
    if sub_states:
        for sub_state_name, sub_state in sub_states.items():
            sub_state_transitions = get_transitions_recurse( sub_state )
            if sub_state_transitions:
                transitions_list += sub_state_transitions
                #print( f'394 transitions_list = {json.dumps( transitions_list, indent = 2 )}' )
    
    assert( isinstance( transitions_list, list ) )
    return transitions_list

####################################################################################################
# Searches the model for any transitions which either leave or enter the given state.
def get_relevant_transitions( state: dict ) -> list:
    assert( isinstance( state, dict ) )

    tree_path = state.get_tree_path()
    #print( f'405 tree_path = {json.dumps( tree_path, indent = 2 )}' )

    transitions = get_relevant_transitions_recurse( curr_model )
    #print( f'408 Model trans = {json.dumps( transitions, indent = 2 )}' )

    # Filter for the transitions relevant to the state of interest.
    relevant_transitions = []
    for transition in transitions:
        src_tree_path = transition.get( hsm_defaults.RSVD_SRC, "" )
        dst_tree_path = transition.get( hsm_defaults.RSVD_DEST, "" )
        if compare_tree_paths( tree_path, src_tree_path ):
            relevant_transitions.append( transition )
        elif compare_tree_paths( tree_path, dst_tree_path ):
            relevant_transitions.append( transition )

    assert( isinstance( relevant_transitions, list ) )
    if ( len( relevant_transitions ) > 0 ):
        for relevant_transition in relevant_transitions:
            assert( isinstance( relevant_transition, dict ) )
    return relevant_transitions


####################################################################################################
# TODO: Figure out the best places for these assertions.
#    if state.name == hsm_defaults.RSVD_START:
#        assert( len( transitions ) == 1 )
#        assert( hsm_defaults.RSVD_AUTO in transitions )
#
#    # The final state can have no transitions out of it.
#    assert( hsm_defaults.RSVD_TRAN not in state.model )

import io
import os
import json


HSM_DEFAULT_FILENAME = "hsm_model.json"
DEFAULT_SM_NAME = "unnamed state"
MIN_SM_WID = 60
MIN_SM_HGT = 50
DEFAULT_SM_REC = f"""{{
    "name": {DEFAULT_SM_NAME},
    "lft": 0,
    "top": 0,
    "wid": {MIN_SM_WID},
    "hgt": {MIN_SM_HGT}
}}"""


class sm_model:
    def __init__( self, model_root: object, model_parent: object, lft: int, top: int, wid: int, hgt: int ):
        self.root = model_root
        self.parent = model_parent
        # Start by deserializing the default JSON model.
        self.model = json.load( DEFAULT_SM_REC )
        self.set_value( ["lft"], lft )
        self.set_value( ["top"], top )
        self.set_value( ["wid"], wid )
        self.set_value( ["hgt"], hgt )

    # Read a value from the model.
    # If the value is set, the string is returned. If not set, None is returned.
    #
    # Preconditions:
    # self.model is a dictionary which has been populated.
    #
    # Invariants:
    # No model variables, are modified during this call.
    #
    # Postconditions:
    # None.
    #
    # Returns:
    # A valid value from the model, or None if not previously set.
    def get_value( self, key_chain: list, default_value ) -> str:
        num_levels = len( key_chain )
        assert( num_levels > 0 )
        
        # Drill down into the model along the designated branch.
        model_section = self.model
        for key in key_chain:
            try:
                model_section = model_section[ key ]
            except KeyError:
                return None

        try:
            value = str( model_section )
        except:
            print( f"WARN: Unable to convert {model_section} to string." )
            return None
            
        return value

    # Update a setting.
    #
    # Preconditions:
    # self.model is a dictionary which has been populated.
    #
    # Invariants:
    # No model values outside the key_chain entry, are modified during this call.
    #
    # Postconditions:
    # The value is stored as a string at the branch indexed by key_chain.
    def set_value( self, key_chain: list, new_value ) -> None:
        assert( len( key_chain ) > 0 )
        
        # Drill down into the model along the designated branch.
        model_section = self.model
        for key in key_chain[ : -1 ]:
            try:
                model_section = model_section[ key ]
            except KeyError:
                # This key is not yet in the settings, add it.
                model_section[ key ] = {}
                self.root.model_has_changed = True
                model_section = model_section[ key ]

        # Only set the value if it has changed.
        if model_section[ key_chain[ -1 ] ] != str( new_value ):
            model_section[ key_chain[ -1 ] ] = str( new_value )
            self.root.model_has_changed = True
            print( f"SM Set: keys = {key_chain}, new_val = {new_value}" )

    # Read the state machine's widget (upper left) position from the model.
    #
    # Preconditions:
    # self.model is a dictionary which has been populated.
    #
    # Invariants:
    # No model variables are modified during this call.
    #
    # Postconditions:
    # Model is identical to before the call.
    #
    # Returns:
    # An x and y tuple for the widget.
    # Note: x and/or y can be None, check before using.
    def get_posn( self ) -> ( int, int ):
        lft_str = self.get_value( [ "lft" ] )
        lft = None
        
        if lft_str != None:
            # This form allows for alternate number bases (i.e. hex strings).
            lft = int( lft_str, 0 )
        
        top_str = self.get_value( [ "top" ] )
        top = None
        
        if top_str != None:
            # This form allows for alternate number bases (i.e. hex strings).
            top = int( top_str, 0 )
        
        return ( lft, top )

    # Set the state machine widget's position in the model.
    #
    # Preconditions:
    # self.model is a dictionary which has been populated.
    #
    # Invariants:
    # No settings outside the state machine's left and top positions are modified during this call.
    #
    # Postconditions:
    # left and/or top in the model is updated.
    def set_posn( self, lft: int = 0, top: int = 0 ) -> None:
        if ( lft < 0 ):
            lft = 0
        self.set_value( [ "lft" ], lft )

        if ( top < 0 ):
            top = 0
        self.set_value( [ "top" ], top )

    # Read the state machine's widget width and height from the model.
    #
    # Preconditions:
    # self.model is a dictionary which has been populated.
    #
    # Invariants:
    # No model variables are modified during this call.
    #
    # Postconditions:
    # Model is identical to before the call.
    #
    # Returns:
    # A width and height tuple for the widget.
    # Note: width and/or height can be None, check before using.
    def get_size( self ) -> ( int, int ):
        wid_str = self.get_value( [ "wid" ] )
        wid = None
        
        if wid_str != None:
            # This form allows for alternate number bases (i.e. hex strings).
            wid = int( wid_str, 0 )
        
        hgt_str = self.get_value( [ "hgt" ] )
        hgt = None
        
        if hgt_str != None:
            # This form allows for alternate number bases (i.e. hex strings).
            hgt = int( hgt_str, 0 )
        
        return ( wid, hgt )

    # Set the state machine widget's size in the model.
    #
    # Preconditions:
    # self.model is a dictionary which has been populated.
    #
    # Invariants:
    # No settings outside the state machine's width and height are modified during this call.
    #
    # Postconditions:
    # width and/or height in the model is updated.
    def set_size( self, wid: int = MIN_SM_WID, hgt: int = MIN_SM_HGT ) -> None:
        if ( wid < MIN_SM_WID ):
            wid = MIN_SM_WID
        self.set_value( [ "wid" ], wid )

        if ( hgt < MIN_SM_HGT ):
            hgt = MIN_SM_HGT
        self.set_value( [ "hgt" ], hgt )



# The "database" containing the State Machines, Transitions, Actions, and Events in this design.
class hsm_model:
    # Preconditions:
    # pygame.init() has been called, and pygame.display.set_mode(...) has not yet been called.
    def __init__( self, filename: str = HSM_DEFAULT_FILENAME ):
        self.model_has_changed = False

        # See if the model file exists in the current folder.
        self.model_filename = filename
        if not os.path.isfile( filename ):
            # File isn't here, create a default model in the current folder.
            print( f"WARN: File {filename} not found when loading model file." )
            self.create_default_model()
        
        # Deserialize the JSON settings.
        try:
            model_file = open( self.model_filename, "r" )
            if not model_file:
                print( f"WARN: There is something wrong with the file {self.model_filename}, and it can't be opened." )
                print( f"WARN: Examine the path and file and make sure it contains valid JSON text." )
                print( f"WARN: Continuing with an empty model." )
                self.model = json.loads( DEFAULT_SM_REC )
                return

            try:
                self.model = json.load( sess_file )
            except json.JSONDecodeError as e:
                print( f"ERR: JSONDecodeError, {e.msg}, file=\"{self.model_filename}\", line = {e.lineno}, col = {e.colno}." )
                self.create_default_model()
                
            model_file.close()
        except FileNotFoundError:
            self.create_default_model()

    def create_default_model( self ) -> None:
        # Reset the filename to ensure a valid default.
        self.model_filename = DEFAULT_FILENAME
        print( f"INFO: Creating default model file {self.model_filename}." )

        try:
            model_file = open( self.model_filename, "w" )
            model_file.write( DEFAULT_JSON )
            model_file.close()
        except IOError:
            print( f"ERR: Unable to create file {self.model_filename}" )

        try:
            self.model = json.loads( DEFAULT_JSON )
        except json.JSONDecodeError as e:
            print( f"ERR: JSONDecodeError, {e.msg}, str=\"{DEFAULT_JSON}\", line = {e.lineno}, col = {e.colno}." )
            exit()
    
    # Write any settings changes to disk.
    def sync_to_disk( self ) -> None:
        print( f"INFO: Updating \"{self.model_filename}\" to {self.model}" )
        if ( self.model_has_changed ):
            model_file = open( self.model_filename, "w" )
            json.dump( self.model, model_file, ensure_ascii = True, indent = 4 )
            model_file.close()
            self.model_has_changed = False

    # Read a value from the model.
    # If valid, return that. If not:
    #   Set the value to the supplied default.
    #
    # Preconditions:
    # self.model is a dictionary which has been populated.
    #
    # Invariants:
    # No model variables outside the key_chain entry, are modified during this call.
    #
    # Postconditions:
    # Either the pre-call value, or if not yet set, the default value as provided.
    #
    # Returns:
    # A valid value, first from the model, or using defaults if not previously set.
    def get_value( self, key_chain: list, default_value ) -> str:
        num_levels = len( key_chain )
        assert( num_levels > 0 )
        
        # Drill down into the model along the designated branch.
        model_section = self.model
        for key in key_chain:
            try:
                model_section = model_section[ key ]
            except KeyError:
                # This key is not yet in the model, add it.
                if ( num_levels > 1 ):
                    model_section[ key ] = {}
                else:
                    model_section[ key ] = str( default_value )
                self.model_has_changed = True
                model_section = model_section[ key ]
            num_levels -= 1

        value = str( default_value )
        try:
            value = str( model_section )
        except:
            print( f"WARN: Unable to convert {model_section} to string. Using default of {value} instead." )
            pass
            
        return value

    # Update a setting.
    #
    # Preconditions:
    # self.model is a dictionary which has been populated.
    #
    # Invariants:
    # No model values outside the key_chain entry, are modified during this call.
    #
    # Postconditions:
    # The value is stored as a string at the branch indexed by key_chain.
    def set_value( self, key_chain: list, new_value ) -> None:
        assert( len( key_chain ) > 0 )
        
        # Drill down into the model along the designated branch.
        model_section = self.model
        for key in key_chain[ : -1 ]:
            try:
                model_section = model_section[ key ]
            except KeyError:
                # This key is not yet in the settings, add it.
                model_section[ key ] = {}
                self.model_has_changes = True
                model_section = model_section[ key ]

        if model_section[ key_chain[ -1 ] ] != str( new_value ):
            model_section[ key_chain[ -1 ] ] = str( new_value )
            self.model_has_changes = True
            #print( f"Set: keys = {key_chain}, new_val = {new_value}" )

    def get_new_state_name( self ):
        return "State_1"

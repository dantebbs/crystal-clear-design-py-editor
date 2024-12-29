
import json

# A Most Recently Used tracker with JSON (de)serialize for a list of strings.
class mru:
    def __init__( self, start_list: list = None, max_len: int = 10 ):
        assert( max_len > 0 )
        self.max_len = max_len
        # Implementation is such that the most recently used entry is at
        # the end of the list, i.e. self.entries[ -1 ]
        self.entries = []
        
        # See if the list should be pre-populated.
        if start_list and len( start_list ) > 0:
            #start_list = start_list.replace( "'", '"' )
            #self.entries = json.loads( start_list )
            self.entries = start_list
            #print( f"self.entries = { self.entries }, type = { type( self.entries ) }" )

    # This adds an item if not already in the list, and makes it the most recent.
    def touch( self, entry: str ) -> None:
        # First see if the entry is already the MRU.
        if len( self.entries ) > 0 and entry == self.entries[ -1 ]:
            return
        
        # If a copy was already existing earlier in the list, remove it.
        if entry in self.entries:
            self.entries.remove( entry );
        
        # If the list would become too long, drop the oldest entry.
        if len( self.entries ) + 1 > self.max_len:
            self.entries.pop( 0 )
        
        # Add it to the end (which also makes it the most recent).
        self.entries.append( entry )
        #print( f"Latest model = {self.get_at_idx()}" )

    # Returns the number of entries in the list.
    def len( self ) -> int:
        return len( self.entries )

    # Returns entries from indexed list positions for valid indexes.
    # Returns None for invalid indexes or when list is empty.
    # Note: Index 0 is the least recently used, index -1 is the most recently used.
    # Note: Calling without an index returns
    def get_at_idx( self, idx: int = -1 ):
        if idx >= 0:
            if idx < len( self.entries ):
                return self.entries[ idx ]
            else:
                return None
        else:
            if abs( idx ) <= len( self.entries ):
                return self.entries[ idx ]
            else:
                return None

    # This is an accessor for the purpose of saving the list to disk.
    def get_list( self ) -> list:
        return self.entries


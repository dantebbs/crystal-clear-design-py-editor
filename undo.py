####################################################################################################
# Store actions and related data in a FILO stack.
#
# Undo-able actions and their parameters are defined and managed by their respective modules.
# This module is a "blind" container that simply manages the stack.
# As a convenience, this module also implements the "dirty" flag (needs-to-be-saved flag).


####################################################################################################
def mark_changes_as_saved():
    return

####################################################################################################
def have_unsaved_changes():
    return

####################################################################################################
class undoable_actions():
    def __init__( self ):
        self.actions = []

    def action_done( self, action_definition: dict ):
        if not callback in action_definition:
            throw "action_definition must include the callback method"

        return

####################################################################################################
# A convenience routine to search for a function of the given name.
# The current code space is searched for a function matching the given name, and if valid, the
# function is called with the parameters.
# param[in]  undo_func  Defines function to be called, and any parameters.
#                       Example, "set_indicator(red, 50)" would cause the set_indicator function to
#                       be called with the 2 parameters of red, and fifty.
def run_undo_function(undo_func: str, callback_module: object) -> bool:
    all_funcs_returned_true = True

    # The function and any parameters must be in valid python syntax.
    # Check that while simultaneously breaking out the function name
    # and the parameters.
    match = re.search("^([a-zA-Z_]\w*)\((.*(,.*)*)\)$", undo_func)
    if match:
        function_name = match.group(1)
        params = match.group(2)
        print( f"Calling undo function: {str(callback_module)}.{function_name}({params})" )

        func = getattr(callback_module, function_name)
        if func:
            func(params)
        else:
            raise NotImplementedError(f"Function {function_name}() not implemented!")

    return all_funcs_returned_true

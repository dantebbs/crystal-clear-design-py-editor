import traceback

def showstack():
    for line in traceback.format_stack():
        print( line.strip() )

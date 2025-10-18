import traceback

def showstack():
    for line in traceback.format_stack():
        print( line.strip() )

# These 3 helper functions check for / find the intersection of lines in a 2-D plane.
def ccw( A: dict, B: dict, C: dict ) -> bool:
    return ( C[ "y" ] - A[ "y" ] ) * ( B[ "x" ] - A[ "x" ] ) > ( B[ "y" ] - A[ "y" ] ) * ( C[ "x" ] - A[ "x" ] )

# Return true if line segments AB and CD intersect
def do_lines_intersect( A: dict, B: dict, C: dict, D: dict ) -> bool:
    #print( f"li: A = {A}\n    B = {B}\n    C = {C}\n    D = {D}" )
    return ccw( A, C, D ) != ccw( B, C, D ) and ccw( A, B, C ) != ccw( A, B, D )

# Return the intersection point if line segments AB and CD intersect, otherwise returns None.
# Formula:
# Given lines (a1, a2) and (b1, b2) and the intersection p
# (if the denominator is zero, the lines have no unique intersection),
#     | | a1 a2 |  a1 - a2 |
#     | | b1 b2 |  b1 - b2 |
# p = ----------------------
#      | a1 - a2  b1 - b2 |
def line_intersection(line1, line2) -> dict:
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
       return None

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return {'x': int( round( x ) ), 'y': int( round( y ) ) }    


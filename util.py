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

def point_to_line_dist( point, line ) -> int:
    dist = int( 0 )
    
    # From Wikipedia https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line
    # Given a non-vertical and non-horizontal line of the form P1 = (x1,y1) to P2 = (x2,y2) and point (x0, y0):
    #                               | ( y2 - y1 ) x0 - ( x2 - x1 ) y0 + x2 y1 = y2 x1 |
    #  dist( P1, P2, ( x0, y0 ) ) = ---------------------------------------------------
    #                                      sqrt( ( y2 - y1 )^2 + ( x2 - x1 )^2 )
    # Note: If needed, there is available an optimization using the area of the triangle.
    ( x0, y1, x1, y1, x2, y2 ) = ( point[0], point[1], line[0][0], line[0][1], line[1][0], line[1][1] )
    ( x_dist, y_dist ) = ( x2 - x1, y2 - y1 )
    if ( y_dist == 0 ):
        # Special case of a horizontal line.
        dist = int( x_dist )
    elif ( x_dist == 0 ):
        # Special case of a vertical line.
        dist = int( y_dist )
    else:
        numerator = abs( ( y_dist * x0 ) - ( x_dist * x1 ) + ( x2 * y1 ) - ( y2 * x1 ) )
        denominator = sqrt( ( y_dist * y_dist ) + ( x_dist * x_dist ) )
        dist = int( round( numerator / denominator ) )
    
    return dist
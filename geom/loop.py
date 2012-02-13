
from pymunk import moment_for_poly, Poly


class Loop(object):

    density = 1

    def __init__(self, verts=None):
        if verts is None:
            verts = []
        self.verts = verts
        if not self.is_clockwise():
            self.verts.reverse()


    def get_signed_area(self):
        """
        Return area of a simple (ie. non-self-intersecting) polygon.
        If verts wind anti-clockwise, this returns a negative number.
        Assume y-axis points up.
        """
        accum = 0.0
        for i in range(len(self.verts)):
            j = (i + 1) % len(self.verts)
            accum += (
                self.verts[j][0] * self.verts[i][1] -
                self.verts[i][0] * self.verts[j][1])
        return accum / 2


    def get_area(self):
        '''
        Always returns a positive number. If poly is self-intersecting, the
        actual area will be smaller than this.
        '''
        return abs(self.get_signed_area())


    def is_clockwise(self):
        '''
        Assume y-axis points up
        '''
        retval = self.get_signed_area() > 0
        return self.get_signed_area() > 0

        
    def get_mass(self):
        return self.get_area() * self.density


    def get_centroid(self):
        x, y = 0, 0
        for i in xrange(len(self.verts)):
            j = (i + 1) % len(self.verts)
            factor = (
                self.verts[j][0] * self.verts[i][1] -
                self.verts[i][0] * self.verts[j][1])
            x += (self.verts[i][0] + self.verts[j][0]) * factor
            y += (self.verts[i][1] + self.verts[j][1]) * factor
        polyarea = self.get_area()
        x /= 6 * polyarea
        y /= 6 * polyarea
        return (x, y) 


    def get_moment(self):
        return moment_for_poly(self.get_mass(), self.verts, (0, 0))


    def offset(self, x, y):
        self.verts = [
            (self.verts[i][0] + x, self.verts[i][1] + y)
            for i in xrange(len(self.verts))
        ]


    def get_shape(self, body):
        shape = Poly(body, self.verts, (0, 0))
        shape.elasticity = 0.5
        shape.friction = 10.0
        return shape


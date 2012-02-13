import pymunk as pm

from svg_model.seidel import Triangulator


class BodyGroup(object):
    def __init__(self, paths=None):
        # Create virtual space to add bodies to.  Each body will act as a sensor to
        # detect clicking, etc. on a path in the SVG.
        self.space = pm.Space()
        self.bodies = {}
        self.reverse_bodies = {}
        if paths is None:
            self.paths = {}
        else:
            self.paths = paths
            for name, geo_path in self.paths.iteritems():
                self.add_path(name, geo_path)

    def add_path(self, name, geo_path):
        body = pm.Body()
        for loop in geo_path.loops:
            # Triangulate/tessellate path, since pymunk only supports convex paths.
            # We will add all triangles resulting from the tessellation as shapes
            # for the body.  That way, clicks on any of the triangles will be
            # detected as a click on this body.
            triangulator = Triangulator(loop.verts)
            triangles = triangulator.triangles()
            for triangle in triangles:
                shape = pm.Poly(body, triangle)
                self.space.add_static(shape)
        self.bodies[name] = body
        self.reverse_bodies[body] = name

    def get_body(self, name):
        return self.bodies[name]

    def get_name(self, body):
        return self.reverse_bodies[body]



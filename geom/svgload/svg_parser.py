
import xml.dom.minidom

from shapely.geometry import MultiPoint

from path_parser import PathParser

from geom.loop import Loop
from geom.path import Path


class Svg(object):
    '''
    Maintains an ordered list of paths, each one corresponding to a path tag
    from an SVG file. Creates a pylget Batch containing all these paths, for
    rendering as a single OpenGL GL_TRIANGLES indexed vert primitive.
    '''
    def __init__(self):
        self.paths = {}
        self.path_order = []


    def add_path(self, id, path):
        self.paths[id] = path
        self.path_order.append(id)


    def add_to_batch(self, batch):
        '''
        Adds paths to the given batch object. They are all added as
        GL_TRIANGLES, so the batch will aggregate them all into a single OpenGL
        primitive.
        '''
        for name in self.path_order:
            path = self.paths[name]
            path.add_to_batch(batch)


    def get_boundary(self):
        if 'boundary' in self.paths:
            boundary = self.paths['boundary']
        else:
            boundary = Path([self.convex_hull()])
        return boundary


    def all_verts(self):
        for path in self.paths.itervalues():
            for loop in path.loops:
                for vert in loop.verts:
                    yield vert


    def convex_hull(self):
        points = list(self.all_verts())
        multipoint = MultiPoint(points)
        hullpoints = [v for v in multipoint.convex_hull.exterior.coords][:-1]
        return Loop(hullpoints)


class SvgParser(object):
    '''
    parse(filename) returns an Svg object, populated from the <path> tags
    in the file.
    '''
    def parse(self, filename):
        svg = Svg()
        doc = xml.dom.minidom.parse(filename)       
        path_tags = doc.getElementsByTagName('path')
        parser = PathParser()
        for path_tag in path_tags:
            id, path = parser.parse(path_tag)
            svg.add_path(id, path)

        #x, y = svg.get_boundary().get_centroid()
        x, y = svg.get_boundary().get_center()
        for path in svg.paths.values():
            path.offset(-x, -y)
        return svg


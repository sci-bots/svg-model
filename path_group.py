from svgload.svg_parser import SvgParser


class PathGroup(object):
    def __init__(self, paths, boundary):
        self.paths = paths
        self._boundary = boundary
        self._bounding_box = self._boundary.get_bounding_box()

    @classmethod
    def load_svg(cls, svg_path):
        # Parse SVG file.
        parser = SvgParser()
        svg = parser.parse(svg_path)
        paths = svg.paths
        boundary = svg.get_boundary()
        del svg
        del parser
        return PathGroup(paths, boundary)

    def get_bounding_box(self):
        return self._bounding_box

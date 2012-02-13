from svgload.svg_parser import SvgParser


class SvgPathGroup(object):
    def __init__(self, svg_path):
        # Parse SVG file.
        parser = SvgParser()
        svg = parser.parse(svg_path)
        self.paths = svg.paths
        self._boundary = svg.get_boundary()
        self._bounding_box = self._boundary.get_bounding_box()
        del svg
        del parser

    def get_bounding_box(self):
        return self._bounding_box

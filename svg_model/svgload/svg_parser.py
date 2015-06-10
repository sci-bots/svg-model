'''
This is a New BSD License.
http://www.opensource.org/licenses/bsd-license.php

Copyright (c) 2008-2009, Jonathan Hartley (tartley@tartley.com)
Copyright (c) 2012, Christian Fobel (christian@fobel.net)
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    * Neither the name of Jonathan Hartley nor the names of contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''
import warnings
from collections import OrderedDict

from lxml import etree
from path_helpers import path
from .path_parser import PathParser, ParseError
from ..loop import Loop
from ..geo_path import Path


class SvgParseError(Exception):
    pass


def parse_warning(*args):
    filename, tag, message = args
    msg = 'Error parsing %s:%d, %s\n    %s'
    if filename:
        filename = filename.name
    warnings.warn(msg % (filename, tag.sourceline, message,
            etree.tostring(tag)), RuntimeWarning)


class Svg(object):
    '''
    Maintains an ordered list of paths, each one corresponding to a path tag
    from an SVG file. Creates a pylget Batch containing all these paths, for
    rendering as a single OpenGL GL_TRIANGLES indexed vert primitive.
    '''
    def __init__(self):
        self.paths = OrderedDict()

    def add_path(self, id, path):
        self.paths[id] = path

    def add_to_batch(self, batch):
        '''
        Adds paths to the given batch object. They are all added as
        GL_TRIANGLES, so the batch will aggregate them all into a single OpenGL
        primitive.
        '''
        for name in self.paths:
            svg_path = self.paths[name]
            svg_path.add_to_batch(batch)

    def get_bounding_box(self):
        points = list(self.all_verts())
        x_vals = zip(*points)[0]
        y_vals = zip(*points)[1]
        min_x, min_y = min(x_vals), min(y_vals)
        max_x, max_y = max(x_vals), max(y_vals)
        return Loop([(min_x, min_y), (min_x, max_y), (max_x, max_y),
                (max_x, min_y)])

    def get_boundary(self):
        if 'boundary' in self.paths:
            boundary = self.paths['boundary']
        else:
            boundary = Path([self.get_bounding_box()])
        return boundary

    def all_verts(self):
        for svg_path in self.paths.itervalues():
            for loop in svg_path.loops:
                for vert in loop.verts:
                    yield vert


class SvgParser(object):
    '''
    parse(filename) returns an Svg object, populated from the <path> tags
    in the file.

    '''
    def parse_file(self, filename, on_error=None):
        self.filename = path(filename)
        xml_root = etree.parse(self.filename)
        return self.parse(xml_root, on_error)

    def parse(self, xml_root, on_error=None):
        '''
        Parse all <path> elements from xml_root.

        Optional on_error arg specifies a callback function to be run when
        an error occurs during parsing.
        The specified on_error function must accept 3 arguments:
            <svg filename>, <path_tag>, <error message>
        An example on_error handler is provided as svg_load.svg_parser.parse_warning(),
        where all SvgParseErrors are converted to warning messages.  See usage below:
        >>> import re
        >>> svg_parser = SvgParser()
        >>> path_tag = etree.XML("""
        ...     <path
        ...     xmlns="http://www.w3.org/2000/svg"
        ...     xmlns:dc="http://purl.org/dc/elements/1.1/"
        ...     xmlns:cc="http://creativecommons.org/ns#"
        ...     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        ...     xmlns:svg="http://www.w3.org/2000/svg"
        ...     xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
        ...     xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
        ...     id="path13231"
        ...     d="M8 4 l-4,4"
        ...     linecap="square"
        ...     stroke="#000000"
        ...     stroke-width="0.25"
        ...     />""")
        >>> with warnings.catch_warnings(record=True) as w:
        ...     svg = svg_parser.parse(path_tag, on_error=parse_warning)
        >>> print w[-1].category
        <type 'exceptions.RuntimeWarning'>
        >>> match = re.search(r'^Error parsing None:\d+, unsupported svg path command: l', str(w[-1].message))
        >>> print match is None
        False
        >>> path_tag = etree.XML("""
        ...     <path
        ...     xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
        ...     xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:cc="http://creativecommons.org/ns#"
        ...     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
        ...     xmlns:svg="http://www.w3.org/2000/svg"
        ...     xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
        ...     style="fill:#0000ff;stroke:#ff0000;stroke-width:0.10000000000000001;stroke-miterlimit:4;stroke-dasharray:none"
        ...     id="path18327"
        ...     d="M 636.0331,256.9345 L 636.0331,256.9345"
        ...     inkscape:connector-curvature="0"/>""")
        >>> with warnings.catch_warnings(record=True) as w:
        ...     svg = svg_parser.parse(path_tag, on_error=parse_warning)
        >>> print w[-1].category
        <type 'exceptions.RuntimeWarning'>
        >>> match = re.search(r'^Error parsing None:\d+, loop needs 3 or more verts', str(w[-1].message))
        >>> print match is None
        False
        '''
        svg = Svg()
        svg_namespace = {'svg': 'http://www.w3.org/2000/svg'}
        path_tags = xml_root.xpath('(/svg:svg|/svg:svg/svg:g)/svg:path',
                                   namespaces=svg_namespace)
        parser = PathParser()
        for path_tag in path_tags:
            try:
                id, svg_path = parser.parse(path_tag)
                if svg_path.loops:
                    svg.add_path(id, svg_path)
            except (ParseError, ), why:
                filename = getattr(self, 'filename', None)
                args = (filename, path_tag, why.message)
                if on_error:
                    on_error(*args)
                else:
                    raise SvgParseError(*args)

        if svg.paths:
            x, y = svg.get_boundary().get_center()
            for svg_path in svg.paths.values():
                svg_path.offset(-x, -y)
        return svg

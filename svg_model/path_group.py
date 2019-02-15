'''
This is a New BSD License.
http://www.opensource.org/licenses/bsd-license.php

Copyright (c) 2012, Christian Fobel (christian@fobel.net)
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    * Neither the name of Jonathan Hartley nor the names of contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
'''
from __future__ import absolute_import
from __future__ import unicode_literals
from .svgload.svg_parser import SvgParser


class PathGroup(object):
    def __init__(self, paths, boundary):
        self.paths = paths
        self._boundary = boundary
        self._bounding_box = self._boundary.get_bounding_box()

    @classmethod
    def load_svg(cls, svg_path, on_error=None):
        # Parse SVG file.
        parser = SvgParser()
        svg = parser.parse_file(svg_path, on_error)
        paths = svg.paths
        if not paths:
            raise Exception("File has no valid paths.")
        boundary = svg.get_boundary()
        del svg
        del parser
        return PathGroup(paths, boundary)

    def get_bounding_box(self):
        return self._bounding_box

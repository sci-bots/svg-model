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
from .loop import Loop


class Path(object):
    '''
    A Path is a list of loops.
    '''
    def __init__(self, loops):
        self.loops = []
        for loop in loops:
            if not isinstance(loop, Loop):
                loop = Loop(loop)
            self.loops.append(loop)


    def get_area(self):
        return sum(loop.get_area() for loop in self.loops)


    def get_mass(self):
        return sum(loop.get_mass() for loop in self.loops)

    def get_center(self):
        x, y, width, height = self.get_bounding_box()
        return x + width / 2., y + height / 2.

    def get_centroid(self):
        x, y = 0, 0
        for loop in self.loops:
            loopx, loopy = loop.get_centroid()
            x += loopx * loop.get_mass()
            y += loopy * loop.get_mass()
        if len(self.loops) > 0:
            area = self.get_area()
            x /= area
            y /= area
        return (x, y)


    def get_moment(self):
        return sum(loop.get_moment() for loop in self.loops)


    def offset(self, x, y):
        for loop in self.loops:
            loop.offset(x, y)


    def offset_to_origin(self):
        x, y = self.get_centroid()
        for loop in self.loops:
            loop.offset(-x, -y)

    def get_bounding_box(self):
        from itertools import chain
        x_vals = list(chain(*[zip(*loop.verts)[0] for loop in self.loops]))
        y_vals = list(chain(*[zip(*loop.verts)[1] for loop in self.loops]))
        min_x, min_y = min(x_vals), min(y_vals)
        max_x, max_y = max(x_vals), max(y_vals)
        return (min_x, min_y, max_x - min_x, max_y - min_y)


class ColoredPath(Path):

    def __init__(self, loops):
        Path.__init__(self, loops)
        self.color = (0, 0, 0)


    def _serialise_verts(self, triangles):
        for vert in triangles:
            yield vert[0]
            yield vert[1]

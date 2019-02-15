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
import pymunk as pm

from .seidel import Triangulator
import six


class BodyGroup(object):
    def __init__(self, paths=None):
        # Create virtual space to add bodies to.  Each body will act as a
        # sensor to detect clicking, etc. on a path in the SVG.
        self.space = pm.Space()
        self.bodies = {}
        self.reverse_bodies = {}
        if paths is None:
            self.paths = {}
        else:
            self.paths = paths
            for name, geo_path in six.iteritems(self.paths):
                self.add_path(name, geo_path)

    def add_path(self, name, geo_path):
        body = pm.Body()
        for loop in geo_path.loops:
            # Triangulate/tessellate path, since pymunk only supports convex
            # paths. We will add all triangles resulting from the tessellation
            # as shapes for the body.  That way, clicks on any of the triangles
            # will be detected as a click on this body.
            try:
                triangulator = Triangulator(loop.verts)
            except:
                raise Exception("There was a problem tesselating path %s." % \
                                name)
            triangles = triangulator.triangles()
            for triangle in triangles:
                shape = pm.Poly(body, triangle)
                self.space.add(shape)
        self.bodies[name] = body
        self.reverse_bodies[body] = name

    def get_body(self, name):
        return self.bodies[name]

    def get_name(self, body):
        return self.reverse_bodies[body]

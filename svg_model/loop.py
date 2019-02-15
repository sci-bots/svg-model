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
#from pymunk import moment_for_poly, Poly


from __future__ import unicode_literals
from six.moves import range
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
        return self.get_signed_area() > 0


    def get_mass(self):
        return self.get_area() * self.density


    def get_centroid(self):
        x, y = 0, 0
        for i in range(len(self.verts)):
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


    #def get_moment(self):
        #return moment_for_poly(self.get_mass(), self.verts, (0, 0))


    def offset(self, x, y):
        self.verts = [
            (self.verts[i][0] + x, self.verts[i][1] + y)
            for i in range(len(self.verts))
        ]


    #def get_shape(self, body):
        #shape = Poly(body, self.verts, (0, 0))
        #shape.elasticity = 0.5
        #shape.friction = 10.0
        #return shape


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
from __future__ import unicode_literals
from ..loop import Loop
from ..geo_path import ColoredPath


class ParseError(Exception):
    pass


class PathDataParser(object):

    def __init__(self):
        self.data = None
        self.pos = 0

    def get_char(self, allowed):
        if self.pos < len(self.data) and self.data[self.pos] in allowed:
            self.pos += 1
            return self.data[self.pos - 1]

    def get_chars(self, allowed):
        start = self.pos
        while self.get_char(allowed):
            pass
        return self.data[start:self.pos]

    def get_number(self):
        '''
        .. versionchanged:: 0.9.2
            Add support for float exponent strings (e.g., ``3.435e-7``).

            Fixes `issue #4 <https://github.com/wheeler-microfluidics/svg-model/issues/4>`.
        '''
        number = None
        start = self.get_char('0123456789.-')
        if start:
            number = start
            finish = self.get_chars('-e0123456789.')
            if finish:
                number += finish
        if any(c in number for c in '.e'):
            return float(number)
        else:
            return int(number)

    def to_tuples(self, data):
        '''
        path_data : string, from an svg path tag's 'd' attribute, eg:
            'M 46,74 L 35,12 l 53,-13 z'
        returns the same data collected in a list of tuples, eg:
            [ ('M', 46, 74), ('L', 35, 12), ('l', 53, -13), ('z') ],
        The input data may have floats instead of ints, this will be reflected
        in the output. The input may have its whitespace stripped out, or its
        commas replaced by whitespace.
        '''
        self.data = data
        self.pos = 0
        parsed = []
        command = []

        while self.pos < len(self.data):
            indicator = self.data[self.pos]
            if indicator == ' ':
                self.pos += 1
            elif indicator == ',':
                if len(command) >= 2:
                    self.pos += 1
                else:
                    msg = 'unexpected comma at %d in %r' % (self.pos, self.data)
                    raise ParseError(msg)
            elif indicator in '0123456789.-':
                if command:
                    command.append(self.get_number())
                else:
                    msg = 'missing command at %d in %r' % (self.pos, self.data)
                    raise ParseError(msg)
            else:
                if command:
                    parsed.append(tuple(command))
                command = [indicator]
                self.pos += 1

        if command:
            parsed.append(tuple(command))

        if parsed[0][0] == 'M' and parsed[-1][0] == 'L'\
                and parsed[0][1:] == parsed[-1][1:]:
            parsed[-1] = ('z',)
        return parsed


class LoopTracer(object):
    def __init__(self):
        self.loops = []

    def get_point(self, command):
        x = command[1]
        y = command[2]
        return x, y

    def onVerticalMove(self, command):
        y = command[1]
        prev_x, prev_y = self.current_loop[-1]
        if command[0] == 'v':
            new_y = prev_y + y
        else:
            new_y = y
        self.current_loop.append((prev_x, new_y))

    def onHorizontalMove(self, command):
        x = command[1]
        prev_x, prev_y = self.current_loop[-1]
        if command[0] == 'h':
            new_x = prev_x + x
        else:
            new_x = x
        self.current_loop.append((new_x, prev_y))

    def onMove(self, command):
        x, y = self.get_point(command)
        self.current_loop = [(x, y)]

    def onLine(self, command):
        x, y = self.get_point(command)
        self.current_loop.append((x, y))

    def onClose(self, command):
        if self.current_loop[0] == self.current_loop[-1]:
            self.current_loop = self.current_loop[:-1]
        if len(self.current_loop) < 3:
            raise ParseError('loop needs 3 or more verts')
        loop = Loop(self.current_loop)
        self.loops.append(loop)
        self.current_loop = None

    def onBadCommand(self, action):
        msg = 'unsupported svg path command: %s' % (action,)
        raise ParseError(msg) 

    def to_loops(self, commands):
        '''
        commands : list of tuples, as output from to_tuples() method, eg:
            [('M', 1, 2), ('L', 3, 4), ('L', 5, 6), ('z')]
        Interprets the command characters at the start of each tuple to return
        a list of loops, where each loop is a closed list of verts, and each
        vert is a pair of ints or floats, eg:
            [[1, 2, 3, 4, 5, 6]]
        Note that the final point of each loop is eliminated if it is equal to
        the first.
        SVG defines commands:
            M x,y: move, start a new loop
            L x,y: line, draw boundary
            H x: move horizontal
            V y: move vertical
            Z: close current loop - join to start point
        Lower-case command letters (eg 'm') indicate a relative offset.
        See http://www.w3.org/TR/SVG11/paths.html
        '''
        lookup = {
            'M': self.onMove,
            'L': self.onLine,
            'H': self.onHorizontalMove,
            'h': self.onHorizontalMove,
            'V': self.onVerticalMove,
            'v': self.onVerticalMove,
            'Z': self.onClose,
            'z': self.onClose,
        }
        self.loops = []
        self.current_loop = None

        for command in commands:
            action = command[0]
            if action in lookup:
                lookup[action](command)
            else:
                self.onBadCommand(action)
        return self.loops



class PathParser(object):
    '''
    parse(path_tag) returns an SvgPath object()
    '''
    next_id = 1


    def get_id(self, attributes):
        if 'id' in list(attributes.keys()):
            return attributes['id']
        else:
            self.next_id += 1
            return self.next_id - 1


    def parse_color(self, color):
        '''
        color : string, eg: '#rrggbb' or 'none'
        (where rr, gg, bb are hex digits from 00 to ff)
        returns a triple of unsigned bytes, eg: (0, 128, 255)
        '''
        if color == 'none':
            return None
        return (
            int(color[1:3], 16),
            int(color[3:5], 16),
            int(color[5:7], 16))


    def parse_style(self, style):
        '''
        style : string, eg:
            fill:#ff2a2a;fill-rule:evenodd;stroke:none;stroke-width:1px;
            stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1
        returns color as a triple of unsigned bytes: (r, g, b), or None
        '''
        style_elements = style.split(';')
        while style_elements:
            element = style_elements.pop()
            if element.startswith('fill:'):
                return self.parse_color(element[5:])
        return None


    def parse(self, tag):
        '''
        returns (id, path)
        where:  'id' is the path tag's id attribute
                'path' is a populated instance of SvgPath

        >>> from lxml import etree
        >>> from lxml.builder import E
        >>> path_tag = etree.XML("""
        ...     <path id="path0"
        ...         style="fill:#0000ff;stroke:#000000;stroke-width:0.10000000000000001;stroke-miterlimit:4;stroke-dasharray:none"
        ...         d="M 525.93385,261.47322 L 525.933 85,269.65826 L 534.07239,269.65826 L 534.07239,261.47322 L 525.93385,261.47322" />
        ... """)
        >>> path_parser = PathParser()
        >>> id, svg_path = path_parser.parse(path_tag)
        >>> id
        'path0'
        >>> svg_path.color
        (0, 0, 255)
        >>> len(svg_path.loops)
        1
        >>> svg_path.loops[0].verts
        [(534.07239, 261.47322), (534.07239, 269.65826), (525.933, 85), (525.93385, 261.47322)]

        Note that only absolute commands (i.e., uppercase) are currently supported.  For example:
        paths will throw a ParseError exception.  For example:

        >>> path_tag = E.path(id="path0", d="M 636.0331,256.9345 l 636.0331,256.9345")
        >>> print etree.tostring(path_tag)
        <path d="M 636.0331,256.9345 l 636.0331,256.9345" id="path0"/>
        >>> path_parser.parse(path_tag)
        Traceback (most recent call last):
        ...
        ParseError: unsupported svg path command: l
        >>> 
        '''
        id = self.get_id(tag.attrib)
        
        parser = PathDataParser()
        path_data = tag.attrib['d']
        path_tuple = parser.to_tuples(path_data)

        tracer = LoopTracer()
        loops = tracer.to_loops(path_tuple)
        path = ColoredPath(loops)

        if 'style' in list(tag.attrib.keys()):
            style_data = tag.attrib['style']
            path.color = self.parse_style(style_data)

        return id, path


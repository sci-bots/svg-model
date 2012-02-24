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
import gtk

from svg_model.body_group import BodyGroup
from svg_model.path_group import PathGroup

if __name__ == '__main__':
    path_group = PathGroup.load_svg('circles.svg')
    body_group = BodyGroup(path_group.paths)


    def translate(coords, x, y):
        return [(c[0] + x, c[1] + y) for c in coords]


    def on_click(widget, event):
        x, y, width, height = path_group.get_bounding_box()
        coords = translate([event.get_coords()], -width / 2., -height / 2.)[0]
        shape = body_group.space.point_query_first(coords)
        if shape:
            print body_group.get_name(shape.body)


    window = gtk.Window()
    drawing_area = gtk.DrawingArea()
    drawing_area.set_size_request(640, 480)
    window.add(drawing_area)
    window.show_all()

    cr = drawing_area.window.cairo_create()


    def draw_path(context, p):
        context.save()
        print 'draw_path color', [v / 255. for v in p.color]
        context.set_source_rgb(*[v / 255. for v in p.color])
        for loop in p.loops:
            context.move_to(*loop.verts[0])
            for v in loop.verts[1:]:
                context.line_to(*v)
            context.close_path()
            context.fill()
        context.restore()


    def draw_rectangle():
        cr.rectangle(0, 0, 100, 100)
        cr.set_source_rgb(0, 0.5, 0)
        cr.fill()


    def draw_paths(*args, **kwargs):
        x, y, width, height = path_group.get_bounding_box()
        cr.save()
        cr.translate(width / 2., height / 2.)
        for p in body_group.paths.values():
            draw_path(cr, p)
        cr.restore()


    drawing_area.add_events(gtk.gdk.BUTTON_PRESS_MASK)
    drawing_area.connect('button-press-event', on_click)
    window.connect('destroy', lambda x: gtk.main_quit())

    gtk.main()

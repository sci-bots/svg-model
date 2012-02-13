import gtk

from body_group import SvgBodyGroup

if __name__ == '__main__':
    body_group = SvgBodyGroup('circles.svg')

    def translate(coords, x, y):
        return [(c[0] + x, c[1] + y) for c in coords]


    def on_click(widget, event):
        x, y, width, height = body_group.get_bounding_box()
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
        x, y, width, height = body_group.get_bounding_box()
        cr.save()
        cr.translate(width / 2., height / 2.)
        for p in body_group.paths.values():
            draw_path(cr, p)
        cr.restore()


    drawing_area.add_events(gtk.gdk.BUTTON_PRESS_MASK)
    drawing_area.connect('button-press-event', on_click)

import gtk
import pymunk as pm
from geom.svgload.svg_parser import SvgParser
from seidel import Triangulator


parser = SvgParser()
svg = parser.parse('circles.svg')

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
    x, y, width, height = svg.get_boundary().get_bounding_box()
    cr.save()
    cr.translate(width / 2., height / 2.)
    for p in svg.paths.values():
        draw_path(cr, p)
    cr.restore()

space = pm.Space()
electrodes = {}

def translate(coords, x, y):
    return [(c[0] + x, c[1] + y) for c in coords]

x, y, width, height = svg.get_boundary().get_bounding_box()
for name, p in svg.paths.iteritems():
    body = pm.Body()
    for loop in p.loops:
        triangulator = Triangulator(loop.verts)
        triangles = triangulator.triangles()
        #print translate(loop.verts, width / 2., height / 2.)
        for triangle in triangles:
            shape = pm.Poly(body, triangle)
            #shape = pm.Poly(body, translate(triangle, width / 2., height / 2.))
            space.add_static(shape)
    electrodes[name] = body

reverse_electrodes = dict([(v, k) for k, v in electrodes.iteritems()])

def on_click(widget, event):
    coords = translate([event.get_coords()], -width / 2., -height / 2.)[0]
    shape = space.point_query_first(coords)
    if shape:
        print reverse_electrodes[shape.body]

drawing_area.add_events(gtk.gdk.BUTTON_PRESS_MASK)
drawing_area.connect('button-press-event', on_click)

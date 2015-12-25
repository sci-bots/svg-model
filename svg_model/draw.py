# coding: utf-8
import cStringIO as StringIO

import svgwrite
from svgwrite.path import Path as Path_
from svgwrite.shapes import Polygon

from . import INKSCAPE_NSMAP


def draw_shapes_svg_layer(df_shapes, shape_i_columns, layer_name,
                          layer_number=1, use_svg_path=True):
    '''
    Draw shapes as a layer in a SVG file.

    Args:

        df_shapes (pandas.DataFrame): Table of shape vertices (one row per
            vertex).
        shape_i_columns (str, list) : Either a single column name as a string
            or a list of column names in `df_shapes`.  Rows in `df_shapes` with
            the same value in the `shape_i_columns` column(s) are grouped
            together as a shape.
        layer_name (str) : Name of Inkscape layer.
        layer_number (int) : Z-order index of Inkscape layer.
        use_svg_path (bool) : If `True`, electrodes are drawn as `svg:path`
            elements.  Otherwise, electrodes are drawn as `svg:polygon`
            elements.

    Returns:

        (StringIO.StringIO) : A file-like object containing SVG XML source.
            The XML contains a layer named according to `layer_name`, which in
            turn contains `svg:polygon` or `svg:path` elements corresponding to
            the shapes in the input `df_shapes` table.
    '''
    # Note that `svgwrite.Drawing` requires a filepath to be specified during
    # construction, *but* nothing is actually written to the path unless one of
    # the `save*` methods is called.
    #
    # In this function, we do *not* call any of the `save*` methods.  Instead,
    # we use the `write` method to write to an in-memory file-like object.
    minx, miny = df_shapes[['x', 'y']].min().values
    maxx, maxy = df_shapes[['x', 'y']].max().values
    width = maxx - minx
    height = maxy - miny

    dwg = svgwrite.Drawing('should_not_exist.svg', size=(width, height),
                           debug=False)

    nsmap = INKSCAPE_NSMAP

    dwg.attribs['xmlns:inkscape'] = nsmap['inkscape']

    svg_root = dwg.g(id='layer%d' % layer_number,
                     **{'inkscape:label': layer_name,
                        'inkscape:groupmode': 'layer'})

    minx, miny = df_shapes[['x', 'y']].min().values

    for shape_i, df_shape_i in df_shapes.groupby(shape_i_columns):
        attr_columns = [c for c in df_shape_i.columns
                        if c not in ('vertex_i', 'x', 'y')]
        attrs = df_shape_i.iloc[0][attr_columns].to_dict()
        vertices = df_shape_i[['x', 'y']].values.tolist()
        if not use_svg_path:
            # Draw electrode shape as an `svg:polygon` element.
            p = Polygon(vertices, debug=False, **attrs)
        else:
            # Draw electrode shape as an `svg:path` element.
            commands = ['M %s,%s' % tuple(vertices[0])]
            commands += ['L %s,%s' % tuple(v) for v in vertices[1:]]
            while vertices[0] == vertices[-1]:
                # Start is equal to end of path, but we will use the `'Z'`
                # command to close the path, so delete the last point in the
                # path.
                del vertices[-1]
            commands += ['Z']
            p = Path_(d=' '.join(commands), debug=False, **attrs)
        svg_root.add(p)
    dwg.add(svg_root)

    # Write result to `StringIO`.
    output = StringIO.StringIO()
    dwg.write(output)
    output.seek(0)

    return output


def draw_lines_svg_layer(df_endpoints, layer_name, layer_number=1):
    '''
    Draw lines defined by endpoint coordinates as a layer in a SVG file.

    Args:

        df_endpoints (pandas.DataFrame) : Each row corresponds to the endpoints
            of a single line, encoded through the columns: `x_source`,
            `y_source`, `x_target`, and `y_target`.
        layer_name (str) : Name of Inkscape layer.
        layer_number (int) : Z-order index of Inkscape layer.

    Returns:

        (StringIO.StringIO) : A file-like object containing SVG XML source.
            The XML contains a layer named `"Connections"`, which in turn
            contains one line per row in the input `df_endpoints` table.
    '''
    # Note that `svgwrite.Drawing` requires a filepath to be specified during
    # construction, *but* nothing is actually written to the path unless one of
    # the `save*` methods is called.
    #
    # In this function, we do *not* call any of the `save*` methods.  Instead,
    # we use the `write` method to write to an in-memory file-like object.
    dwg = svgwrite.Drawing('should_not_exist.svg', profile='tiny', debug=False)

    dwg.attribs['width'] = df_endpoints[['x_source', 'x_target']].values.max()
    dwg.attribs['height'] = df_endpoints[['y_source', 'y_target']].values.max()

    nsmap = INKSCAPE_NSMAP

    dwg.attribs['xmlns:inkscape'] = nsmap['inkscape']

    coord_columns = ['x_source', 'y_source', 'x_target', 'y_target']

    line_layer = dwg.g(id='layer%d' % layer_number,
                       **{'inkscape:label': layer_name,
                          'inkscape:groupmode': 'layer'})

    for i, (x1, y1, x2, y2) in df_endpoints[coord_columns].iterrows():
        line_i = dwg.line((x1, y1), (x2, y2), id='line%d' % i,
                          style='stroke:#000000; stroke-width:0.1;')
        line_layer.add(line_i)
    dwg.add(line_layer)

    output = StringIO.StringIO()
    dwg.write(output)
    # Rewind file.
    output.seek(0)
    return output

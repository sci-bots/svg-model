# coding: utf-8
import types

from lxml import etree

from .connections import extract_adjacent_shapes
from .draw import draw_lines_svg_layer
from . import INKSCAPE_NSMAP, compute_shape_centers, svg_shapes_to_df


def auto_detect_adjacent_shapes(svg_source, shape_i_column,
                                layer_name='Connections', shapes_xpath=None,
                                extend=1.5):
    '''
    Attempt to automatically find "adjacent" shapes in a SVG layer, and on a
    second SVG layer, draw each detected connection between the center points
    of the corresponding shapes.

    Args:

        svg_source (str) : Input SVG file as a filepath (or file-like object).

    Returns:

        (cStringIO.StringIO) : File-like object containing SVG document with
            layer named according to `layer_name` with the detected connections
            drawn as `svg:line` instances.
    '''
    if not isinstance(shape_i_column, types.StringType):
        raise KeyError('Shape index must be a single column.')

    # Read SVG polygons into dataframe, one row per polygon vertex.
    if shapes_xpath is None:
        kwargs = {}
    else:
        kwargs = {shapes_xpath}
    df_shapes = svg_shapes_to_df(svg_source, **kwargs)
    df_shapes = compute_shape_centers(df_shapes, shape_i_column)
    df_shape_connections = extract_adjacent_shapes(df_shapes, shape_i_column,
                                                   extend=extend)

    # Parse input file.
    xml_root = etree.parse(svg_source)
    svg_root = xml_root.xpath('/svg:svg', namespaces=INKSCAPE_NSMAP)[0]

    # Get the center coordinate of each shape.
    df_shape_centers = (df_shapes.drop_duplicates(subset=[shape_i_column])
                        [[shape_i_column] + ['x_center', 'y_center']]
                        .set_index(shape_i_column))

    # Get the center coordinate of the shapes corresponding to the two
    # endpoints of each connection.
    df_connection_centers = (df_shape_centers.loc[df_shape_connections.source]
                             .reset_index(drop=True)
                             .join(df_shape_centers.loc[df_shape_connections
                                                        .target]
                                   .reset_index(drop=True), lsuffix='_source',
                                   rsuffix='_target'))

    # Remove existing connections layer from source, in-memory XML (source file
    # remains unmodified).  A new connections layer will be added below.
    connections_xpath = '//svg:g[@inkscape:label="%s"]' % layer_name
    connections_groups = svg_root.xpath(connections_xpath,
                                        namespaces=INKSCAPE_NSMAP)

    if connections_groups:
        for g in connections_groups:
            g.getparent().remove(g)

    # Create in-memory SVG
    svg_output = \
        draw_lines_svg_layer(df_connection_centers
                             .rename(columns={'x_center_source': 'x_source',
                                              'y_center_source': 'y_source',
                                              'x_center_target': 'x_target',
                                              'y_center_target': 'y_target'}),
                             layer_name=layer_name)

    return svg_output

# coding: utf-8
import types

from lxml import etree

from .connections import extract_adjacent_shapes, draw_lines_svg_layer
from . import INKSCAPE_NSMAP, compute_shape_centers, svg_polygons_to_df


def auto_detect_adjacent_shapes(svg_source, shape_i_columns,
                                shapes_xpath=None,
                                connections_layer='Connections'):
    '''
    Attempt to automatically find "adjacent" shapes in a SVG layer, and on a
    second SVG layer, draw each detected connection between the center points
    of the corresponding shapes.

    Args:

        svg_source (str) : Input SVG file as a filepath (or file-like object).

    Returns:

        (lxml.etree.ElementTree) : Root node of XML source tree for SVG
            containing a copy of the original SVG file source, along with an
            additional layer containing the detected connections drawn as
            `svg:line` instances.
    '''
    if isinstance(shape_i_columns, types.StringType):
        shape_i_columns = [shape_i_columns]

    # Read SVG polygons into dataframe, one row per polygon vertex.
    if shapes_xpath is None:
        kwargs = {}
    else:
        kwargs = {shapes_xpath}
    df_shapes = svg_polygons_to_df(svg_source, **kwargs)
    df_shapes = compute_shape_centers(df_shapes, shape_i_columns)
    df_shape_connections = extract_adjacent_shapes(df_shapes, extend=1.5)

    # Parse input file.
    xml_root = etree.parse(svg_source)
    svg_root = xml_root.xpath('/svg:svg', namespaces=INKSCAPE_NSMAP)[0]

    df_shape_centers = (df_shapes.drop_duplicates(subset=shape_i_columns)
                        [shape_i_columns + ['x_center', 'y_center']]
                        .set_index(shape_i_columns))
    df_shape_centers.head()
    df_connection_centers = (df_shape_centers.loc[df_shape_connections.source]
                             .reset_index(drop=True)
                             .join(df_shape_centers.loc[df_shape_connections.target]
                                   .reset_index(drop=True), lsuffix='_source',
                                   rsuffix='_target'))

    # Remove existing connections layer from source, in-memory XML (source file
    # remains unmodified).  A new connections layer will be added below.
    connections_xpath = '//svg:g[@inkscape:label="%s"]' % connections_layer
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
                                              'y_center_target': 'y_target'}))
    xml_lines_root = etree.parse(svg_output)

    connections_group = xml_lines_root.xpath(connections_xpath,
                                             namespaces=INKSCAPE_NSMAP)[0]
    svg_root.append(connections_group)

    return xml_root

# coding: utf-8
# Copyright 2015
# Jerry Zhou <jerryzhou@hotmail.ca> and Christian Fobel <christian@fobel.net>
import warnings

import pandas as pd
import numpy as np

from . import INKSCAPE_NSMAP
from .draw import draw_lines_svg_layer as _draw_lines_svg_layer


def extend_shapes(df_shapes, axis, distance):
    '''
    Extend shape/polygon outline away from polygon center point by absolute
    distance.
    '''
    df_shapes_i = df_shapes.copy()
    offsets = df_shapes_i[axis + '_center_offset'].copy()
    offsets[offsets < 0] -= distance
    offsets[offsets >= 0] += distance
    df_shapes_i[axis] = df_shapes_i[axis + '_center'] + offsets
    return df_shapes_i


def extract_adjacent_shapes(df_shapes, shape_i_column, extend=.5):
    '''
    Generate list of connections between "adjacent" polygon shapes based on
    geometrical "closeness".

    Arguments
    ---------

     - `df_shapes`: Table of polygon shape vertices (one row per vertex).
         * Table rows with the same value in the `path_id` column are grouped
           together as a polygon.
    '''
    # Find corners of each solid shape outline.
    # Extend x coords by abs units
    df_scaled_x = extend_shapes(df_shapes, 'x', extend)
    # Extend y coords by abs units
    df_scaled_y = extend_shapes(df_shapes, 'y', extend)

    df_corners = df_shapes.groupby(shape_i_column).agg({'x': ['min', 'max'],
                                                        'y': ['min', 'max']})

    # Find adjacent electrodes
    row_list = []

    for shapeNumber in df_shapes[shape_i_column].drop_duplicates():
        df_stretched = df_scaled_x[df_scaled_x[shape_i_column]
                                   .isin([shapeNumber])]
        xmin_x, xmax_x, ymin_x, ymax_x = (df_stretched.x.min(),
                                          df_stretched.x.max(),
                                          df_stretched.y.min(),
                                          df_stretched.y.max())
        df_stretched = df_scaled_y[df_scaled_y[shape_i_column]
                                   .isin([shapeNumber])]
        xmin_y, xmax_y, ymin_y, ymax_y = (df_stretched.x.min(),
                                          df_stretched.x.max(),
                                          df_stretched.y.min(),
                                          df_stretched.y.max())

        #Some conditions unnecessary if it is assumed that electrodes don't overlap
        adjacent = df_corners[
            ((df_corners.x['min'] < xmax_x) & (df_corners.x['max'] >= xmax_x)
            # Check in x stretched direction
            |(df_corners.x['min'] < xmin_x) & (df_corners.x['max'] >= xmin_x))
            # Check if y is within bounds
            & (df_corners.y['min'] < ymax_x) & (df_corners.y['max'] > ymin_x) |

            #maybe do ymax_x - df_corners.y['min'] > threshold &
            #  df_corners.y['max'] - ymin_x > threshold

            ((df_corners.y['min'] < ymax_y) & (df_corners.y['max'] >= ymax_y)
             # Checks in y stretched direction
             |(df_corners.y['min'] < ymin_y) & (df_corners.y['max'] >= ymin_y))
             # Check if x in within bounds
            & ((df_corners.x['min'] < xmax_y) & (df_corners.x['max'] > xmin_y))
        ].index.values

        for shape in adjacent:
            temp_dict = {}
            reverse_dict = {}

            temp_dict ['source'] = shapeNumber
            reverse_dict['source'] = shape
            temp_dict ['target'] = shape
            reverse_dict['target'] = shapeNumber

            if(reverse_dict not in row_list):
                row_list.append(temp_dict)

    df_connected = (pd.DataFrame(row_list)[['source', 'target']]
                    .sort(axis=1, ascending=True).sort(['source', 'target']))
    return df_connected


def get_adjacency_matrix(df_connected):
    '''
    Return matrix where $a_{i,j} = 1$ indicates polygon $i$ is connected to
    polygon $j$.

    Also, return mapping (and reverse mapping) from original keys in
    `df_connected` to zero-based integer index used for matrix rows and
    columns.
    '''
    sorted_path_keys = np.sort(np.unique(df_connected[['source', 'target']]
                                         .values.ravel()))
    indexed_paths = pd.Series(sorted_path_keys)
    path_indexes = pd.Series(indexed_paths.index, index=sorted_path_keys)

    adjacency_matrix = np.zeros((path_indexes.shape[0], ) * 2, dtype=int)
    for i_key, j_key in df_connected[['source', 'target']].values:
        i, j = path_indexes.loc[[i_key, j_key]]
        adjacency_matrix[i, j] = 1
        adjacency_matrix[j, i] = 1
    return adjacency_matrix, indexed_paths, path_indexes


def extract_connections(svg_source, shapes_canvas, line_layer='Connections',
                        line_xpath=None, namespaces=None):
    '''
    Load all lines from a layer of an SVG source.  For each line, if endpoints
    overlap distinct shapes in `shapes_canvas`, add connection between
    overlapped shapes.

    Args:

        svg_source (filepath) : Input SVG file containing connection lines.
        shapes_canvas (shapes_canvas.ShapesCanvas) : Shapes canvas containing
            shapes to compare against connection endpoints.
        line_layer (str) : Name of layer in SVG containing connection lines.
        line_xpath (str) : XPath string to iterate throught connection lines.
        namespaces (dict) : SVG namespaces (compatible with `etree.parse`).

    Returns:

        (pandas.DataFrame) : Each row corresponds to connection between two
            shapes in `shapes_canvas`, denoted `source` and `target`.
    '''
    from lxml import etree

    if namespaces is None:
        namespaces = INKSCAPE_NSMAP

    e_root = etree.parse(svg_source)
    frames = []

    if line_xpath is None:
        line_xpath = ("//svg:g[@inkscape:label='%s']/svg:line"
                      % line_layer)
    coords_columns = ['x1', 'y1', 'x2', 'y2']

    for line_i in e_root.xpath(line_xpath, namespaces=namespaces):
        line_i_dict = dict(line_i.items())
        values = ([line_i_dict.get('id', None)] +
                  [float(line_i_dict[k]) for k in coords_columns])
        frames.append(values)

    if not frames:
        return pd.DataFrame(None, columns=['source', 'target'])

    df_connection_lines = pd.DataFrame(frames, columns=['id'] + coords_columns)

    df_shape_connections_i = pd.DataFrame([[shapes_canvas.find_shape(x1, y1),
                                            shapes_canvas.find_shape(x2, y2)]
                                           for i, (x1, y1, x2, y2) in
                                           df_connection_lines[coords_columns]
                                           .iterrows()],
                                          columns=['source', 'target'])
    df_shape_connections_i.sort(axis=1, inplace=True)
    df_shape_connections_i['line_id'] = df_connection_lines['id']
    return df_shape_connections_i.dropna()


def draw_lines_svg_layer(df_endpoints, layer_name='Connections'):
    warnings.warn('`draw_lines_svg_layer` has been moved to `svg_model.draw`')
    return _draw_lines_svg_layer(df_endpoints, layer_name=layer_name)

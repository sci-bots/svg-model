from __future__ import absolute_import
from __future__ import unicode_literals
import numpy as np
import pandas as pd
import warnings

from .svgload import svg_parser
import six


def get_shape_areas(df_shapes, shape_i_columns, signed=False):
    '''
    Return a `pandas.Series` indexed by `shape_i_columns` (i.e., each entry
    corresponds to a single shape/polygon), containing the following columns
    the area of each shape.

    If `signed=True`, a positive area value corresponds to a clockwise loop,
    whereas a negative area value corresponds to a counter-clockwise loop.
    '''
    # Make a copy of the SVG data frame since we need to add columns to it.
    df_i = df_shapes.copy()
    df_i['vertex_count'] = (df_i.groupby(shape_i_columns)['x']
                            .transform('count'))
    df_i['area_a'] = df_i.x
    df_i['area_b'] = df_i.y

    # Vector form of [Shoelace formula][1].
    #
    # [1]: http://en.wikipedia.org/wiki/Shoelace_formula
    df_i.loc[df_i.vertex_i == df_i.vertex_count - 1, 'area_a'] *= df_i.loc[df_i.vertex_i == 0, 'y'].values
    df_i.loc[df_i.vertex_i < df_i.vertex_count - 1, 'area_a'] *= df_i.loc[df_i.vertex_i > 0, 'y'].values

    df_i.loc[df_i.vertex_i == df_i.vertex_count - 1, 'area_b'] *= df_i.loc[df_i.vertex_i == 0, 'x'].values
    df_i.loc[df_i.vertex_i < df_i.vertex_count - 1, 'area_b'] *= df_i.loc[df_i.vertex_i > 0, 'x'].values

    area_components = df_i.groupby(shape_i_columns)[['area_a', 'area_b']].sum()
    shape_areas = .5 * (area_components['area_b'] - area_components['area_a'])

    if not signed:
        shape_areas.name = 'area'
        return shape_areas.abs()
    else:
        shape_areas.name = 'signed_area'
        return shape_areas


def get_bounding_boxes(df_shapes, shape_i_columns):
    '''
    Return a `pandas.DataFrame` indexed by `shape_i_columns` (i.e., each row
    corresponds to a single shape/polygon), containing the following columns:

     - `width`: The width of the widest part of the shape.
     - `height`: The height of the tallest part of the shape.
    '''
    xy_groups = df_shapes.groupby(shape_i_columns)[['x', 'y']]
    xy_min = xy_groups.agg('min')
    xy_max = xy_groups.agg('max')

    shapes = (xy_max - xy_min).rename(columns={'x': 'width', 'y': 'height'})
    return xy_min.join(shapes)


def get_shape_infos(df_shapes, shape_i_columns):
    '''
    Return a `pandas.DataFrame` indexed by `shape_i_columns` (i.e., each row
    corresponds to a single shape/polygon), containing the following columns:

     - `area`: The area of the shape.
     - `width`: The width of the widest part of the shape.
     - `height`: The height of the tallest part of the shape.
    '''
    shape_areas = get_shape_areas(df_shapes, shape_i_columns)
    bboxes = get_bounding_boxes(df_shapes, shape_i_columns)
    return bboxes.join(pd.DataFrame(shape_areas))


def get_bounding_box(df_points):
    '''
    Calculate the bounding box of all points in a data frame.
    '''
    xy_min = df_points[['x', 'y']].min()
    xy_max = df_points[['x', 'y']].max()

    wh = xy_max - xy_min
    wh.index = 'width', 'height'
    bbox = pd.concat([xy_min, wh])
    bbox.name = 'bounding_box'
    return bbox


def close_paths(df_svg):
    # Initialize the closing point for each path based on the first point in
    # the path.
    close_points = df_svg.groupby('path_id').nth(0)
    # Set index of closing vertex (point) to next index in sequence for each
    # path.
    close_points.loc[:, 'vertex_i'] = df_svg.groupby('path_id')['path_id'].count()
    return pd.concat([df_svg,
                      close_points.reset_index()]).sort(df_svg.columns[:3]
                                                        .tolist())


def get_nearest_neighbours(path_centers):
    x_m, x_n = np.meshgrid(path_centers.x.values, path_centers.x.values)
    y_m, y_n = np.meshgrid(path_centers.y.values, path_centers.y.values)

    distances = np.sqrt((x_m - x_n) ** 2 + (y_m - y_n) ** 2)

    nearest_neighbour_i = (np.finfo(distances.dtype).max *
                           np.eye(distances.shape[0]) +
                           distances).argmin(axis=1)
    nearest_centers = path_centers.iloc[nearest_neighbour_i].reset_index()
    nearest_centers.index = path_centers.index
    nearest_neighbors = path_centers.join(nearest_centers, rsuffix='_closest')
    return nearest_neighbors


# ## Deprecated ##
def get_svg_path_frame(svg_path):
    warnings.warn('get_svg_path_frame function is deprecated.  Use '
                  '`svg_model.svg_polygons_to_df`')
    frames = []
    for i, loop_i in enumerate(svg_path.loops):
        verts = pd.DataFrame(loop_i.verts, columns=['x', 'y'])
        verts.insert(0, 'vertex_i', np.arange(verts.shape[0], dtype=int))
        verts.insert(0, 'loop_i', i)
        frames.append(verts)
    return pd.concat(frames)


# ## Deprecated ##
def get_svg_frame(svg_filepath):
    warnings.warn('get_svg_frame function is deprecated.  Use '
                  '`svg_model.svg_polygons_to_df`')
    parser = svg_parser.SvgParser()
    svg = parser.parse_file(svg_filepath, lambda *args: None)
    frames = []
    for k, p in six.iteritems(svg.paths):
        svg_frame = get_svg_path_frame(p)
        svg_frame.insert(0, 'path_id', k)
        frames.append(svg_frame)
    return pd.concat(frames).reset_index(drop=True)


# ## Deprecated ##
def triangulate_svg_frame(svg_frame):
    warnings.warn('triangulate_svg_frame function is deprecated.  Use '
                  '`svg_model.tesselate.tesselate_shapes_frame`')
    from .seidel import Triangulator

    triangle_frames = []

    for (path_id, loop_i), df_path_i in svg_frame.groupby(['path_id',
                                                           'loop_i']):
        triangulator = Triangulator(df_path_i[['x', 'y']].values)

        for triangle_i, t in enumerate(triangulator.triangles()):
            frame = pd.DataFrame(t, columns=['x', 'y'])
            frame.insert(0, 'path_id', path_id)
            frame.insert(1, 'loop_i', loop_i)
            frame.insert(2, 'triangle_i', triangle_i)
            frame.insert(3, 'vertex_i', np.arange(frame.shape[0]))
            triangle_frames.append(frame)
    return pd.concat(triangle_frames)

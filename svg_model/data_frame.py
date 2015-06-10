import numpy as np
import pandas as pd

from .svgload import svg_parser


def get_svg_path_frame(svg_path):
    frames = []
    for i, loop_i in enumerate(svg_path.loops):
        verts = pd.DataFrame(loop_i.verts, columns=['x', 'y'])
        verts.insert(0, 'vert_i', np.arange(verts.shape[0], dtype=int))
        verts.insert(0, 'loop_i', i)
        frames.append(verts)
    return pd.concat(frames)


def get_svg_frame(svg_filepath):
    parser = svg_parser.SvgParser()
    svg = parser.parse_file(svg_filepath, lambda *args: None)
    frames = []
    for k, p in svg.paths.iteritems():
        svg_frame = get_svg_path_frame(p)
        svg_frame.insert(0, 'path_id', k)
        frames.append(svg_frame)
    return pd.concat(frames).reset_index(drop=True)


def close_paths(df_svg):
    # Initialize the closing point for each path based on the first point in
    # the path.
    close_points = df_svg.groupby('path_id').nth(0)
    # Set index of closing vertex (point) to next index in sequence for each
    # path.
    close_points.loc[:, 'vert_i'] = df_svg.groupby('path_id')['path_id'].count()
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


def get_path_areas(df_svg, signed=False):
    '''
    Return a `pandas.Series` indexed by `path_id`, containing the signed area
    corresponding to each path.  A positive area value corresponds to a clockwise
    loop, whereas a negative area value corresponds to a counter-clockwise loop.
    '''
    # Make a copy of the SVG data frame since we need to add columns to it.
    df_i = df_svg.copy()
    df_i['vert_count'] = df_i.groupby('path_id')['x'].transform('count')
    df_i['area_a'] = df_i.x
    df_i['area_b'] = df_i.y

    # Vector form of [Shoelace formula][1].
    #
    # [1]: http://en.wikipedia.org/wiki/Shoelace_formula
    df_i.loc[df_i.vert_i == df_i.vert_count - 1, 'area_a'] *= df_i.loc[df_i.vert_i == 0, 'y'].values
    df_i.loc[df_i.vert_i < df_i.vert_count - 1, 'area_a'] *= df_i.loc[df_i.vert_i > 0, 'y'].values

    df_i.loc[df_i.vert_i == df_i.vert_count - 1, 'area_b'] *= df_i.loc[df_i.vert_i == 0, 'x'].values
    df_i.loc[df_i.vert_i < df_i.vert_count - 1, 'area_b'] *= df_i.loc[df_i.vert_i > 0, 'x'].values

    area_components = df_i.groupby('path_id')[['area_a', 'area_b']].sum()
    path_areas = .5 * (area_components['area_b'] - area_components['area_a'])

    if not signed:
        path_areas.name = 'area'
        return path_areas.abs()
    else:
        path_areas.name = 'signed_area'
        return path_areas


def get_bounding_boxes(df_svg):
    xy_groups = df_svg.groupby('path_id')[['x', 'y']]
    xy_min = xy_groups.agg('min')
    xy_max = xy_groups.agg('max')

    shapes = (xy_max - xy_min).rename(columns={'x': 'width', 'y': 'height'})
    return xy_min.join(shapes)


def get_path_infos(df_svg):
    path_areas = get_path_areas(df_svg)
    bboxes = get_bounding_boxes(df_svg)
    return bboxes.join(pd.DataFrame(path_areas))


def get_bounding_box(df_svg):
    xy_min = df_svg[['x', 'y']].min()
    xy_max = df_svg[['x', 'y']].max()

    wh = xy_max - xy_min
    wh.index = 'width', 'height'
    bbox = pd.concat([xy_min, wh])
    bbox.name = 'bounding_box'
    return bbox


def triangulate_svg_frame(svg_frame):
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
            frame.insert(3, 'vert_i', np.arange(frame.shape[0]))
            triangle_frames.append(frame)
    return pd.concat(triangle_frames)

# coding: utf-8
import pandas as pd
import pint  # Unit conversion from inches to mm
from .data_frame import get_shape_infos


# Convert Inkscape pixels-per-inch (PPI) to pixels-per-mm (PPmm).
ureg = pint.UnitRegistry()

INKSCAPE_PPI = 90
INKSCAPE_PPmm = INKSCAPE_PPI / ureg.inch.to('mm')


def svg_polygons_to_df(svg_source, xpath='svg:polygon', namespaces=None):
    '''
    Return a `pandas.DataFrame` with one row per vertex for all polygons in
    `svg_source`, with the following columns:

     - `path_id`: The `id` attribute of the corresponding polygon.
     - `vertex_i`: The index of the vertex within the corresponding polygon.
     - `x`: The x-coordinate of the vertex.
     - `y`: The y-coordinate of the vertex.

    Arguments
    ---------

     - `svg_source`: A file path, URI, or file-like object.
    '''
    from lxml import etree

    XHTML_NAMESPACE = "http://www.w3.org/2000/svg"
    NSMAP = {'svg' : XHTML_NAMESPACE}  # map default namespace to prefix 'svg:'

    if namespaces is None:
        namespaces = NSMAP

    e_root = etree.parse(svg_source)
    frames = []

    for polygon_i in e_root.xpath(xpath, namespaces=NSMAP):
        points_i = [[polygon_i.attrib['id'], i] + map(float, v.split(','))
                    for i, v in enumerate(polygon_i.attrib['points']
                                          .strip().split(' '))]
        frames.extend(points_i)
        # # TODO #
        # Add support for:
        #
        #  - fill, stroke
        #  - transform: matrix, scale, etc.
        #      * **N.B.,** This is necessary to map to x,y coords to actual
        #        scale and position.
    return pd.DataFrame(frames, columns=['path_id', 'vertex_i', 'x', 'y'])


def compute_shape_centers(df_shapes, shape_i_columns, inplace=False):
    '''
    Compute the center point of each polygon shape, and the offset of each
    vertex to the corresponding polygon center point.

    Arguments
    ---------

     - `df_shapes`: Table of polygon shape vertices (one row per vertex).
         * Table rows with the same value in the `path_id` column are grouped
           together as a polygon.
    '''
    if not inplace:
        df_shapes = df_shapes.copy()

    # Get coordinates of center of each path.
    df_shapes_info = get_shape_infos(df_shapes, shape_i_columns)
    path_centers = df_shapes_info[['x', 'y']] + .5 * df_shapes_info[['width', 'height']].values
    df_shapes['x_center'] = path_centers.x[df_shapes.path_id].values
    df_shapes['y_center'] = path_centers.y[df_shapes.path_id].values

    # Calculate coordinate of each path vertex relative to center point of path.
    center_offset = df_shapes[['x', 'y']] - df_shapes[['x_center', 'y_center']].values
    return df_shapes.join(center_offset, rsuffix='_center_offset')


def scale_points(df_points, scale=INKSCAPE_PPmm.magnitude, inplace=False):
    '''
    Translate points such that bounding box is anchored at (0, 0) and scale `x`
    and `y` columns of input frame by specified `scale`.

    By default, scale to millimeters based on Inkscape default of 90
    pixels-per-inch.
    '''
    if not inplace:
        df_points = df_points.copy()

    # Offset device, such that all coordinates are >= 0.
    df_points[['x', 'y']] -= df_points[['x', 'y']].min()

    # Scale path coordinates.
    df_points[['x', 'y']] /= scale

    return df_points


def scale_to_fit_a_in_b(a_shape, b_shape):
    '''
    Return scale factor (scalar float) to fit `a_shape` into `b_shape` while
    maintaining aspect ratio.

    Arguments
    ---------

     - `a_shape`: A `pandas.Series`-like object with a `width` and a `height`.
     - `b_shape`: A `pandas.Series`-like object with a `width` and a `height`.
    '''
    # Normalize the shapes to allow comparison.
    a_shape_normal = a_shape / a_shape.max()
    b_shape_normal = b_shape / b_shape.max()

    if a_shape_normal.width > b_shape_normal.width:
        a_shape_normal *= b_shape_normal.width / a_shape_normal.width

    if a_shape_normal.height > b_shape_normal.height:
        a_shape_normal *= b_shape_normal.height / a_shape_normal.height

    return a_shape_normal.max() * b_shape.max() / a_shape.max()


def fit_points_in_bounding_box(df_points, bounding_box, padding_fraction=0):
    '''
    Return dataframe with `x`, `y` columns scaled to fit points from
    `df_points` to fill `bounding_box` while maintaining aspect ratio.

    Arguments
    ---------

     - `df_points`: A `pandas.DataFrame`-like object with `x`, `y` columns,
       containing one row per point.
     - `bounding_box`: A `pandas.Series`-like object with a `width` and a
       `height`.
     - `padding_fraction`: Fraction of padding to add around points.
    '''
    df_scaled_points = df_points.copy()
    offset, padded_scale = fit_points_in_bounding_box_params(df_points,
                                                             bounding_box,
                                                             padding_fraction)
    df_scaled_points[['x', 'y']] *= padded_scale
    df_scaled_points[['x', 'y']] += offset
    return df_scaled_points


def fit_points_in_bounding_box_params(df_points, bounding_box,
                                      padding_fraction=0):
    '''
    Return offset and scale factor to scale `x`, `y` columns of `df_points` to
    fill `bounding_box` while maintaining aspect ratio.

    Arguments
    ---------

     - `df_points`: A `pandas.DataFrame`-like object with `x`, `y` columns,
       containing one row per point.
     - `bounding_box`: A `pandas.Series`-like object with a `width` and a
       `height`.
     - `padding_fraction`: Fraction of padding to add around points.
    '''
    width, height = df_points[['x', 'y']].max()

    points_bbox = pd.Series([width, height], index=['width', 'height'])
    fill_scale = 1 - 2 * padding_fraction
    assert(fill_scale > 0)

    scale = scale_to_fit_a_in_b(points_bbox, bounding_box)

    padded_scale = scale * fill_scale
    offset = .5 * (bounding_box - points_bbox * padded_scale)
    offset.index = ['x', 'y']
    return offset, padded_scale


# ## Deprecated ##
def get_scaled_svg_frame(svg_filepath, **kwargs):
    raise NotImplementedError('get_scaled_svg_frame function is deprecated. '
                              'Use `svg_model.scale_points` and '
                              '`svg_model.compute_shape_centers`')

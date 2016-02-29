# coding: utf-8
import re
import types
import warnings

import pandas as pd
import pint  # Unit conversion from inches to mm
from .data_frame import get_bounding_boxes


XHTML_NAMESPACE = "http://www.w3.org/2000/svg"
NSMAP = {'svg' : XHTML_NAMESPACE}
INKSCAPE_NSMAP = NSMAP.copy()
INKSCAPE_NSMAP['inkscape'] = 'http://www.inkscape.org/namespaces/inkscape'

# Convert Inkscape pixels-per-inch (PPI) to pixels-per-mm (PPmm).
ureg = pint.UnitRegistry()

INKSCAPE_PPI = 90
INKSCAPE_PPmm = INKSCAPE_PPI / (1 * ureg.inch).to('mm')

float_pattern = r'[+-]?\d+(\.\d+)?([eE][+-]?\d+)?'  # 2, 1.23, 23e39, 1.23e-6, etc.
cre_path_command = re.compile(r'(?P<command>[MLZ])\s+(?P<x>%s),\s*(?P<y>%s)\s*'
                              % (float_pattern, float_pattern))


def svg_shapes_to_df(svg_source, xpath='//svg:path | //svg:polygon',
                     namespaces=None):
    '''
    Return a `pandas.DataFrame` with one row per vertex for all shapes (either
    `svg:path` or `svg:polygon`) in `svg_source`, with the following columns:

     - `path_id`: The `id` attribute of the corresponding shape.
     - `vertex_i`: The index of the vertex within the corresponding shape.
     - `x`: The x-coordinate of the vertex.
     - `y`: The y-coordinate of the vertex.

    Arguments
    ---------

     - `svg_source`: A file path, URI, or file-like object.
    '''
    from lxml import etree

    if namespaces is None:
        namespaces = INKSCAPE_NSMAP

    e_root = etree.parse(svg_source)
    frames = []
    attribs_set = set()

    # Get list of attributes that are set in any of the shapes (not including
    # the `svg:path` `"d"` attribute or the `svg:polygon` `"points"`
    # attribute).
    #
    # This, for example, collects attributes such as:
    #
    #  - `fill`, `stroke` (as part of `"style"` attribute)
    #  - `"transform"`: matrix, scale, etc.
    for shape_i in e_root.xpath(xpath, namespaces=namespaces):
        attribs_set.update(shape_i.attrib.keys())

    for k in ('d', 'points'):
        if k in attribs_set:
            attribs_set.remove(k)

    attribs = list(attribs_set)

    # Always add 'id' attribute as first attribute.
    if 'id' in attribs:
        attribs.remove('id')
    attribs.insert(0, 'id')

    for shape_i in e_root.xpath(xpath, namespaces=namespaces):
        # Gather shape attributes from SVG element.
        base_fields = [shape_i.attrib.get(k, None) for k in attribs]

        if shape_i.tag == '{http://www.w3.org/2000/svg}path':
            # Decode `svg:path` vertices from [`"d"`][1] attribute.
            #
            # [1]: https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/d
            points_i = [base_fields + [i] +
                        map(float, [m.group(v) for v in 'xy'])
                        for i, m in enumerate(cre_path_command
                                              .finditer(shape_i.attrib['d']))]
        elif shape_i.tag == '{http://www.w3.org/2000/svg}polygon':
            # Decode `svg:polygon` vertices from [`"points"`][2] attribute.
            #
            # [2]: https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/points
            points_i = [base_fields + [i] + map(float, v.split(','))
                        for i, v in enumerate(shape_i.attrib['points']
                                              .strip().split(' '))]
        else:
            warnings.warning('Unsupported shape tag type: %s' % shape_i.tag)
            continue
        frames.extend(points_i)
    if not frames:
        # There were no shapes found, so set `frames` list to `None` to allow
        # an empty data frame to be created.
        frames = None
    return pd.DataFrame(frames, columns=attribs + ['vertex_i', 'x', 'y'])


def svg_polygons_to_df(svg_source, xpath='//svg:polygon', namespaces=None):
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
    warnings.warn("The `svg_polygons_to_df` function is deprecated.  Use "
                  "`svg_shapes_to_df` instead.")
    result = svg_shapes_to_df(svg_source, xpath=xpath, namespaces=namespaces)
    return result[['id', 'vertex_i', 'x', 'y']].rename(columns={'id':
                                                                'path_id'})


def compute_shape_centers(df_shapes, shape_i_column, inplace=False):
    '''
    Compute the center point of each polygon shape, and the offset of each
    vertex to the corresponding polygon center point.

    Args:

        df_shapes (pandas.DataFrame) : Table of polygon shape vertices (one row
            per vertex).
        shape_i_column (str) : Table rows with the same value in the
            `shape_i_column` column are grouped together as a shape.
        in_place (bool) : If `True`, center coordinate columns are added to the
            input frame. Otherwise, center coordinate columns are added to copy
            of the input frame.
    '''
    if not isinstance(shape_i_column, types.StringType):
        raise KeyError('Shape index must be a single column.')

    if not inplace:
        df_shapes = df_shapes.copy()

    # Get coordinates of center of each path.
    df_bounding_boxes = get_bounding_boxes(df_shapes, shape_i_column)
    path_centers = (df_bounding_boxes[['x', 'y']] + .5 *
                    df_bounding_boxes[['width', 'height']].values)
    df_shapes['x_center'] = path_centers.x[df_shapes[shape_i_column]].values
    df_shapes['y_center'] = path_centers.y[df_shapes[shape_i_column]].values

    # Calculate coordinate of each path vertex relative to center point of
    # path.
    center_offset = (df_shapes[['x', 'y']] -
                     df_shapes[['x_center', 'y_center']].values)
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
    df_points.x -= df_points.x.min()
    df_points.y -= df_points.y.min()

    # Scale path coordinates.
    df_points.x /= scale
    df_points.y /= scale

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
    width = df_points.x.max()
    height = df_points.y.max()

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

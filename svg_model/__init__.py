# coding: utf-8
import pandas as pd
import pint  # Unit conversion from inches to mm
from .data_frame import get_svg_frame, get_path_infos


# Convert Inkscape pixels-per-inch (PPI) to pixels-per-mm (PPmm).
ureg = pint.UnitRegistry()

INKSCAPE_PPI = 90
INKSCAPE_PPmm = INKSCAPE_PPI / ureg.inch.to('mm')


def get_paths_frame_with_centers(df_paths):
    '''
    Compute the center point of each polygon path, and the offset of each vertex to the corresponding polygon center point.

    Arguments
    ---------

     - `df_paths`: Table of polygon path vertices (one row per vertex).
         * Table rows with the same value in the `path_id` column are grouped
           together as a polygon.
    '''
    df_paths = df_paths.copy()
    # Get coordinates of center of each path.
    df_paths_info = get_path_infos(df_paths)
    path_centers = df_paths_info[['x', 'y']] + .5 * df_paths_info[['width', 'height']].values
    df_paths['x_center'] = path_centers.x[df_paths.path_id].values
    df_paths['y_center'] = path_centers.y[df_paths.path_id].values

    # Calculate coordinate of each path vertex relative to center point of path.
    center_offset = df_paths[['x', 'y']] - df_paths[['x_center', 'y_center']].values
    return df_paths.join(center_offset, rsuffix='_center_offset')


def get_scaled_svg_frame(svg_filepath, **kwargs):
    # Read device layout from SVG file.
    df_device = get_svg_frame(svg_filepath)
    return scale_svg_frame(df_device, **kwargs)


def scale_svg_frame(df_device, scale=INKSCAPE_PPmm.magnitude):
    # Offset device, such that all coordinates are >= 0.
    df_device[['x', 'y']] -= df_device[['x', 'y']].min()

    # Scale path coordinates based on Inkscape default of 90 pixels-per-inch.
    df_device[['x', 'y']] /= INKSCAPE_PPmm.magnitude

    df_paths = get_paths_frame_with_centers(df_device)
    return df_paths


def svg_polygons_to_df(svg_source, xpath='svg:polygon', namespaces=None):
    '''
    `svg_source`: A file path, URI, or file-like object.
    '''
    from lxml import etree

    XHTML_NAMESPACE = "http://www.w3.org/2000/svg"
    NSMAP = {'svg' : XHTML_NAMESPACE}  # map default namespace to prefix 'svg:'

    if namespaces is None:
        namespaces = NSMAP

    e_root = etree.parse(svg_source)
    frames = []

    for polygon_i in e_root.xpath(xpath, namespaces=NSMAP):
        frame = (pd.DataFrame([map(float, v.split(','))
                               for v in polygon_i.attrib['points'].strip()
                               .split(' ')],
                              columns=['x', 'y']).reset_index()
                 .rename(columns={'index': 'vertex_i'}))
        frame.insert(0, 'path_id', polygon_i.attrib['id'])
        frames.append(frame)
    return pd.concat(frames).reset_index(drop=True)


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

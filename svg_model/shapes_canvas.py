# coding: utf-8
import types

import numpy as np
import pandas as pd
from . import (svg_polygons_to_df, fit_points_in_bounding_box,
               fit_points_in_bounding_box_params)
from .tesselate import tesselate_shapes_frame
from .point_query import get_shapes_pymunk_space


def get_transform(offset, scale):
    return pd.DataFrame([[scale, 0, offset.x], [0, scale, offset.y],
                         [0, 0, 1]], index=['x', 'y', 'w'])


class ShapesCanvas(object):
    '''
    The `ShapesCanvas` class fits all shapes defined by vertices in a
    `pandas.DataFrame` (one vertex per row) into a specified canvas shape (with
    optional padding), while maintaining aspect ratio.

    The `ShapesCanvas.find_shape` method returns the shape located at the
    specified *canvas* coordinates (or `None`, if no shape intersects with
    specified point).
    '''
    def __init__(self, df_shapes, shape_i_columns, canvas_shape=None,
                 padding_fraction=0):
        '''
        Arguments
        ---------

         - `df_shapes`: A `pandas.DataFrame`-like object with `x`, `y` columns,
           containing one row per point.
         - `shape_i_columns`: Column(s) in `df_shapes` to group points by
           shape.
         - `canvas_shape`: A `pandas.Series`-like object with a `width` and a
           `height`.
        '''
        self.df_shapes = df_shapes
        if isinstance(shape_i_columns, types.StringType):
            shape_i_columns = [shape_i_columns]
        self.shape_i_columns = shape_i_columns

        # Scale and center source points to canvas shape.
        self.source_shape = pd.Series(df_shapes[['x', 'y']].max().values,
                                      index=['width', 'height'])

        # Tesselate electrode polygons into convex shapes (triangles), for
        # compatability with `pymunk`.
        self.df_tesselations = tesselate_shapes_frame(self.df_shapes,
                                                      shape_i_columns)

        # Create `pymunk` space and add a body for each convex shape.  Each
        # body is mapped to the original shape identifier through
        # `canvas_bodies`.
        self.space, self.bodies = get_shapes_pymunk_space(self.df_tesselations,
                                                          shape_i_columns +
                                                          ['triangle_i'])
        self.padding_fraction = padding_fraction
        self.reset_shape(canvas_shape, self.padding_fraction)

    def reset_shape(self, canvas_shape=None, padding_fraction=None):
        if canvas_shape is None:
            canvas_shape = self.source_shape.copy()
        if padding_fraction is None:
            padding_fraction = self.padding_fraction
        self.canvas_shape = canvas_shape

        self.df_canvas_shapes = fit_points_in_bounding_box(self.df_shapes,
                                                           canvas_shape,
                                                           padding_fraction=
                                                           padding_fraction)

        # Compute shape (i.e., width and height) of bounding box for each
        # canvas shape.
        df_bounding_coords = (self.df_canvas_shapes.groupby('id')[['x', 'y']]
                              .agg(['min', 'max']))
        bounding_width = df_bounding_coords.x['max'] - df_bounding_coords.x['min']
        bounding_height = df_bounding_coords.y['max'] - df_bounding_coords.y['min']
        self.df_bounding_shapes = pd.DataFrame(np.column_stack([bounding_width,
                                                                bounding_height]),
                                               columns=['width', 'height'],
                                               index=df_bounding_coords.index)

        if self.df_canvas_shapes.shape[0] == 0:
            self.canvas_offset = pd.Series([0, 0], index=['x', 'y'])
            self.canvas_scale = 1.
        else:
            # Get x/y-offset and scale for later use.
            self.canvas_offset, self.canvas_scale = \
                fit_points_in_bounding_box_params(self.df_shapes, canvas_shape,
                                                  padding_fraction=
                                                  padding_fraction)

        # Create transformation matrix to map from shapes coordinate space to
        # canvas coordinate space.
        self.shapes_to_canvas_transform = get_transform(self.canvas_offset,
                                                        self.canvas_scale)
        self.canvas_to_shapes_transform = \
            np.linalg.inv(self.shapes_to_canvas_transform)

    @classmethod
    def from_svg(cls, svg_filepath, *args, **kwargs):
        # Read SVG polygons into dataframe, one row per polygon vertex.
        df_shapes = svg_polygons_to_df(svg_filepath)

        return cls(df_shapes, 'path_id', *args, **kwargs)

    def find_shape(self, canvas_x, canvas_y):
        '''
        Look up shape based on canvas coordinates.
        '''
        shape_x, shape_y, w = self.canvas_to_shapes_transform.dot([canvas_x,
                                                                   canvas_y,
                                                                   1])
        shape = self.space.point_query_first((shape_x, shape_y))
        if shape:
            return self.bodies[shape.body]
        return None

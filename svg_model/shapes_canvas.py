# coding: utf-8
import types

import pandas as pd
from . import (svg_polygons_to_df, fit_points_in_bounding_box,
               fit_points_in_bounding_box_params)
from .tesselate import tesselate_shapes_frame
from .point_query import get_shapes_pymunk_space


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
        if canvas_shape is None:
            canvas_shape = self.source_shape.copy()
        self.canvas_shape = canvas_shape

        self.df_canvas_shapes = fit_points_in_bounding_box(df_shapes,
                                                           canvas_shape,
                                                           padding_fraction=
                                                           padding_fraction)

        # Get x/y-offset and scale for later use
        self.canvas_offset, self.canvas_scale = \
            fit_points_in_bounding_box_params(df_shapes, canvas_shape,
                                              padding_fraction=
                                              padding_fraction)

        # Tesselate *scaled* shapes into convex shapes and construct pymunk `Space`

        # Tesselate electrode polygons into convex shapes (triangles), for
        # compatability with `pymunk`.
        self.df_canvas_tesselations = \
            tesselate_shapes_frame(self.df_canvas_shapes, shape_i_columns)

        # Create `pymunk` space and add a body for each convex shape.  Each
        # body is mapped to the original `path_id` through `electrode_bodies`.
        self.canvas_space, self.canvas_bodies = \
            get_shapes_pymunk_space(self.df_canvas_tesselations,
                                    shape_i_columns + ['triangle_i'])

    @classmethod
    def from_svg(cls, svg_filepath, *args, **kwargs):
        # Read SVG polygons into dataframe, one row per polygon vertex.
        df_shapes = svg_polygons_to_df(svg_filepath)

        return cls(df_shapes, 'path_id', *args, **kwargs)

    def find_shape(self, canvas_x, canvas_y):
        '''
        Look up shape based on canvas coordinates.
        '''
        shape = self.canvas_space.point_query_first((canvas_x, canvas_y))
        if shape:
            return self.canvas_bodies[shape.body]
        return None

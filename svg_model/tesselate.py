# coding: utf-8
import types

import pandas as pd
from .seidel import Triangulator


def tesselate_shapes_frame(df_shapes, shape_i_columns):
    '''
    Tesselate each shape path into one or more triangles.

    Return `pandas.DataFrame` with columns storing the following fields
    for each row (where each row corresponds to a triangle vertex):

     - `shape_i_columns`: The shape path index column(s).
     - `triangle_i`: The integer triangle index within each electrode path.
     - `vertex_i`: The integer vertex index within each triangle.
    '''
    frames = []
    if isinstance(shape_i_columns, types.StringType):
        shape_i_columns = [shape_i_columns]

    for shape_i, df_path in df_shapes.groupby(shape_i_columns):
        triangulator = Triangulator(df_path[['x', 'y']].values)

        if not isinstance(shape_i, (types.ListType, types.TupleType)):
            shape_i = [shape_i]

        for i, triangle_i in enumerate(triangulator.triangles()):
            triangle_points_i = [shape_i + [i] + [j, x, y]
                                 for j, (x, y) in enumerate(triangle_i)]
            frames.extend(triangle_points_i)
    frames = None if not frames else frames
    return pd.DataFrame(frames, columns=shape_i_columns +
                        ['triangle_i', 'vertex_i', 'x', 'y'])

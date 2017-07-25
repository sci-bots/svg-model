# coding: utf-8
import types

import pandas as pd
from .seidel import Triangulator


def tesselate_shapes_frame(df_shapes, shape_i_columns):
    '''
    Tesselate each shape path into one or more triangles.

    Parameters
    ----------
    df_shapes : pandas.DataFrame
        Table containing vertices of shapes, one row per vertex, with the *at
        least* the following columns:
         - ``x``: The x-coordinate of the vertex.
         - ``y``: The y-coordinate of the vertex.
    shape_i_columns : str or list
        Column(s) forming key to differentiate rows/vertices for each distinct
        shape.

    Returns
    -------
    pandas.DataFrame

    Table where each row corresponds to a triangle vertex, with the following
    columns:

     - ``shape_i_columns[]``: The shape path index column(s).
     - ``triangle_i``: The integer triangle index within each electrode path.
     - ``vertex_i``: The integer vertex index within each triangle.
    '''
    frames = []
    if isinstance(shape_i_columns, types.StringType):
        shape_i_columns = [shape_i_columns]

    for shape_i, df_path in df_shapes.groupby(shape_i_columns):
        points_i = df_path[['x', 'y']].values
        if (points_i[0] == points_i[-1]).all():
            # XXX End point is the same as the start point (do not include it).
            points_i = points_i[:-1]
        triangulator = Triangulator(points_i)
        if not isinstance(shape_i, (types.ListType, types.TupleType)):
            shape_i = [shape_i]

        for i, triangle_i in enumerate(triangulator.triangles()):
            triangle_points_i = [shape_i + [i] + [j, x, y]
                                 for j, (x, y) in enumerate(triangle_i)]
            frames.extend(triangle_points_i)
    frames = None if not frames else frames
    return pd.DataFrame(frames, columns=shape_i_columns +
                        ['triangle_i', 'vertex_i', 'x', 'y'])

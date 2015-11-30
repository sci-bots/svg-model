# coding: utf-8
import types

import pandas as pd
from svg_model.seidel import Triangulator


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
            frame = pd.DataFrame(triangle_i, columns=['x', 'y']).reset_index()
            frame.rename(columns={'index': 'vertex_i'}, inplace=True)
            frame.insert(0, 'triangle_i', i)

            for i in xrange(len(shape_i_columns)):
                frame.insert(i, shape_i_columns[i], shape_i[i])
            frames.append(frame)

    return pd.concat(frames).reset_index(drop=True)

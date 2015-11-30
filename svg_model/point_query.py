# coding: utf-8
import types

import pandas as pd
import pymunk as pm


def get_shapes_pymunk_space(df_convex_shapes, shape_i_columns):
    '''
    Return two-ple containing:

     - A `pymunk.Space` instance.
     - A `pandas.Series` mapping each `pymunk.Body` object in the `Space` to a
       shape index.

    The `Body` to shape index mapping makes it possible to, for example, look
    up the index of the convex shape associated with a `Body` returned by a
    `pymunk` point query in the `Space`.
    '''
    if isinstance(shape_i_columns, types.StringType):
        shape_i_columns = [shape_i_columns]

    space = pm.Space()

    bodies = []

    convex_groups = df_convex_shapes.groupby(shape_i_columns)

    for shape_i, df_i in convex_groups:
        if not isinstance(shape_i, (types.ListType, types.TupleType)):
            shape_i = [shape_i]

        body = pm.Body()
        space.add_static(pm.Poly(body, df_i[['x', 'y']].values))
        bodies.append([body, shape_i[0]])

    return space, (pd.DataFrame(bodies, columns=['body',
                                                 shape_i_columns[0]])
                   .set_index('body')[shape_i_columns[0]])

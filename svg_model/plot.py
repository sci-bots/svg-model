import matplotlib.pyplot as plt
from matplotlib.patches import Polygon


def plot_shapes(df_shapes, shape_i_columns, axis=None, autoxlim=True,
                autoylim=True, **kwargs):
    '''
    Plot shapes from table/data-frame where each row corresponds to a vertex of
    a shape.  Shape vertices are grouped by `shape_i_columns`.

    For example, consider the following dataframe:

            shape_i  vertex_i  x          y
        0   0        0         81.679949  264.69306
        1   0        1         81.679949  286.51788
        2   0        2         102.87004  286.51788
        3   0        3         102.87004  264.69306
        4   1        0         103.11417  264.40011
        5   1        1         103.11417  242.72177
        6   1        2         81.435824  242.72177
        7   1        3         81.435824  264.40011
        8   2        0         124.84134  264.69306
        9   2        1         103.65125  264.69306
        10  2        2         103.65125  286.37141
        11  2        3         124.84134  286.37141

    This dataframe corresponds to three shapes, with (ordered) shape vertices
    grouped by `shape_i`.  Note that the column `vertex_i` is not required.
    '''
    if axis is None:
        fig, axis = plt.subplots()
    colors = axis._get_lines.color_cycle
    color = kwargs.pop('fc', None)

    for shape_i, df_i in df_shapes.groupby(shape_i_columns):
        # Cycle through default colors to set face color, unless face color was
        # set explicitly.
        fc = colors.next() if color is None else color
        poly_patch = Polygon(df_i[['x', 'y']], fc=fc, **kwargs)
        axis.add_patch(poly_patch)

    xy_stats = df_shapes[['x', 'y']].describe()
    if autoxlim:
        axis.set_xlim(*xy_stats.x.loc[['min', 'max']])
    if autoylim:
        axis.set_ylim(*xy_stats.y.loc[['min', 'max']])
    return axis

from collections import OrderedDict
import itertools

from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd


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
    props = itertools.cycle(mpl.rcParams['axes.prop_cycle'])
    color = kwargs.pop('fc', None)

    # Cycle through default colors to set face color, unless face color was set
    # explicitly.
    patches = [Polygon(df_shape_i[['x', 'y']].values, fc=props.next()['color']
                       if color is None else color, **kwargs)
               for shape_i, df_shape_i in df_shapes.groupby(shape_i_columns)]

    collection = PatchCollection(patches)

    axis.add_collection(collection)

    xy_stats = df_shapes[['x', 'y']].describe()
    if autoxlim:
        axis.set_xlim(*xy_stats.x.loc[['min', 'max']])
    if autoylim:
        axis.set_ylim(*xy_stats.y.loc[['min', 'max']])
    return axis


def plot_shapes_heat_map(df_shapes, shape_i_columns, values, axis=None,
                         vmin=None, vmax=None, value_formatter=None,
                         color_map=None):
    '''
    Plot polygon shapes, colored based on values mapped onto
    a colormap.

    Args
    ----

        df_shapes (pandas.DataFrame) : Polygon table containing
            the columns `'id', 'x', 'y'`.  Coordinates must be
            ordered to be grouped by `'id'`.
        values (pandas.Series) : Numeric values indexed by `'id'`.
            These values are used to look up color in the color map.
        axis : A matplotlib axis.  If `None`, an axis is created.
        vmin : Minimum value to clip values at.
        vmax : Maximum value to clip values at.
        color_map : A matplotlib color map (see `matplotlib.cm`).

    Returns
    -------

        (tuple) : First element is heat map axis, second element
            is colorbar axis.
    '''
    df_shapes = df_shapes.copy()

    # Matplotlib draws from bottom to top, so invert `y` coordinates.
    df_shapes.loc[:, 'y'] = df_shapes.y.max() - df_shapes.y.copy().values

    aspect_ratio = ((df_shapes.x.max() - df_shapes.x.min()) /
                    (df_shapes.y.max() - df_shapes.y.min()))

    if vmin is not None or vmax is not None:
        norm = mpl.colors.Normalize(vmin=vmin or min(values),
                                    vmax=vmax or max(values))
    else:
        norm = None

    if axis is None:
        fig, axis = plt.subplots(figsize=(10, 10 * aspect_ratio))
    else:
        fig = axis.get_figure()

    patches = OrderedDict([(id, Polygon(df_shape_i[['x', 'y']].values))
                           for id, df_shape_i in
                           df_shapes.groupby(shape_i_columns)])
    patches = pd.Series(patches)

    collection = PatchCollection(patches.values, cmap=color_map,
                                 norm=norm)
    collection.set_array(values.ix[patches.index])

    axis.add_collection(collection)

    axis_divider = make_axes_locatable(axis)

    # Append color axis to the right of `axis`, with 10% width of `axis`.
    color_axis = axis_divider.append_axes("right", size="10%", pad=0.05)

    colorbar = fig.colorbar(collection, format=value_formatter,
                            cax=color_axis)

    tick_labels = colorbar.ax.get_yticklabels()
    if vmin is not None:
        tick_labels[0] = '$\leq$%s' % tick_labels[0].get_text()
    if vmax is not None:
        tick_labels[-1] = '$\geq$%s' % tick_labels[-1].get_text()
    colorbar.ax.set_yticklabels(tick_labels)

    axis.set_xlim(df_shapes.x.min(), df_shapes.x.max())
    axis.set_ylim(df_shapes.y.min(), df_shapes.y.max())
    return axis, colorbar


def plot_color_map_bars(values, vmin=None, vmax=None, color_map=None,
                        axis=None, **kwargs):
    '''
    Plot bar for each value in `values`, colored based on values mapped onto
    the specified color map.

    Args
    ----

        values (pandas.Series) : Numeric values to plot one bar per value.
        axis : A matplotlib axis.  If `None`, an axis is created.
        vmin : Minimum value to clip values at.
        vmax : Maximum value to clip values at.
        color_map : A matplotlib color map (see `matplotlib.cm`).
        **kwargs : Extra keyword arguments to pass to `values.plot`.

    Returns
    -------

        (axis) : Bar plot axis.
    '''
    if axis is None:
        fig, axis = plt.subplots()

    norm = mpl.colors.Normalize(vmin=vmin or min(values),
                                vmax=vmax or max(values), clip=True)
    if color_map is None:
        color_map = mpl.rcParams['image.cmap']
    colors = color_map(norm(values.values).filled())

    values.plot(kind='bar', ax=axis, color=colors, **kwargs)
    return axis

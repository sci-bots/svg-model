# coding: utf-8
from __future__ import absolute_import
from __future__ import unicode_literals
import sys

from path_helpers import path

from .. import remove_layer
from ..detect_connections import auto_detect_adjacent_shapes
from ..merge import merge_svg_layers


def parse_args(args=None):
    """Parses arguments, returns (options, args)."""
    from argparse import ArgumentParser

    if args is None:
        args = sys.argv

    parser = ArgumentParser(description='''
Attempt to automatically find "adjacent" shapes in a SVG layer, and on a second
SVG layer, draw each detected connection between the center points of the
corresponding shapes.'''.strip())
    parser.add_argument('svg_input_file', type=path, default=None)
    parser.add_argument('svg_output_file', type=path, default="-",
                        help='Output file path ("-" for stdout)', nargs='?')
    parser.add_argument('-f', '--overwrite', action='store_true')

    args = parser.parse_args()

    if not args.overwrite and (args.svg_input_file == args.svg_output_file):
        parser.error('Input and output file are the same.  Use `-f` to force '
                     'overwrite.')

    return args


if __name__ == '__main__':
    args = parse_args()

    connections_svg = auto_detect_adjacent_shapes(args.svg_input_file, 'id')

    # Remove existing "Connections" layer and merge new "Connections" layer
    # with original SVG.
    output_svg = merge_svg_layers([remove_layer(args.svg_input_file,
                                                'Connections'),
                                   connections_svg])

    if args.svg_output_file == '-':
        # Write to standard output stream.
        sys.stdout.write(output_svg.getvalue())
    else:
        with open(args.svg_output_file, 'wb') as output:
            output.write(output_svg.getvalue())

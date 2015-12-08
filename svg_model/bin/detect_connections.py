# coding: utf-8
import sys

from lxml import etree
from path_helpers import path

from ..detect_connections import auto_detect_adjacent_shapes


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
    parser.add_argument('svg_output_file', type=path, default=None)
    parser.add_argument('-f', '--overwrite', action='store_true')

    args = parser.parse_args()

    if not args.overwrite and (args.svg_input_file == args.svg_output_file):
        parser.error('Input and output file are the same.  Use `-f` to force '
                     'overwrite.')

    return args


if __name__ == '__main__':
    args = parse_args()

    output_xml = auto_detect_adjacent_shapes(args.svg_input_file, 'path_id')

    with open(args.svg_output_file, 'wb') as output:
        output.write(etree.tostring(output_xml))

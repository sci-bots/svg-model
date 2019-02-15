# coding: utf-8
from __future__ import absolute_import
from __future__ import unicode_literals
import re


def hex_color_to_rgba(hex_color, normalize_to=255):
    '''
    Convert a hex-formatted number (i.e., `"#RGB[A]"` or `"#RRGGBB[AA]"`) to an
    RGBA tuple (i.e., `(<r>, <g>, <b>, <a>)`).

    Args:

        hex_color (str) : hex-formatted number (e.g., `"#2fc"`, `"#3c2f8611"`)
        normalize_to (int, float) : Factor to normalize each channel by

    Returns:

        (tuple) : RGBA tuple (i.e., `(<r>, <g>, <b>, <a>)`), where range of
            each channel in tuple is `[0, normalize_to]`.
    '''
    color_pattern_one_digit = (r'#(?P<R>[\da-fA-F])(?P<G>[\da-fA-F])'
                               r'(?P<B>[\da-fA-F])(?P<A>[\da-fA-F])?')
    color_pattern_two_digit = (r'#(?P<R>[\da-fA-F]{2})(?P<G>[\da-fA-F]{2})'
                               r'(?P<B>[\da-fA-F]{2})(?P<A>[\da-fA-F]{2})?')

    # First try to match `#rrggbb[aa]`.
    match = re.match(color_pattern_two_digit, hex_color)

    if match:
        channels = match.groupdict()
        channel_scale = 255
    else:
        # Try to match `#rgb[a]`.
        match = re.match(color_pattern_one_digit, hex_color)
        if match:
            channels = match.groupdict()
            channel_scale = 15
        else:
            raise ValueError('Color string must be in format #RGB[A] or '
                             '#RRGGBB[AA] (i.e., alpha channel is optional)')

    scale = normalize_to / channel_scale
    return tuple(type(normalize_to)(int(channels[k], 16) * scale)
                 if channels[k] is not None else None
                 for k in 'RGBA')

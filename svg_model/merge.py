from lxml import etree
import cStringIO as StringIO
import re

import svgwrite

from . import INKSCAPE_NSMAP, INKSCAPE_PPmm

CRE_MM_LENGTH = re.compile(r'^(?P<length>\d+(\.\d+))mm$')


def get_svg_layers(svg_sources):
    '''
    Collect layers from input svg sources.

    Args:

        svg_sources (list) : A list of file-like objects, each containing
            one or more XML layers.

    Returns
    -------
    (width, height), layers : (int, int), list
        The first item in the tuple is the shape of the largest layer, and the
        second item is a list of ``Element`` objects (from :mod:`lxml.etree`
        module), one per SVG layer.
    '''
    layers = []
    width, height = None, None

    def extract_length(attr):
        'Extract length in pixels.'
        match = CRE_MM_LENGTH.match(attr)
        if match:
            # Length is specified in millimeters.
            return INKSCAPE_PPmm.magnitude * float(match.group('length'))
        else:
            return float(attr)

    for svg_source_i in svg_sources:
        # Parse input file.
        xml_root = etree.parse(svg_source_i)
        svg_root = xml_root.xpath('/svg:svg', namespaces=INKSCAPE_NSMAP)[0]
        width = max(extract_length(svg_root.attrib['width']), width)
        height = max(extract_length(svg_root.attrib['height']), height)
        layers += svg_root.xpath('//svg:g[@inkscape:groupmode="layer"]',
                                 namespaces=INKSCAPE_NSMAP)

    for i, layer_i in enumerate(layers):
        layer_i.attrib['id'] = 'layer%d' % (i + 1)
    return (width, height), layers


def merge_svg_layers(svg_sources, share_transform=True):
    '''
    Merge layers from input svg sources into a single XML document.

    Args:

        svg_sources (list) : A list of file-like objects, each containing
            one or more XML layers.
        share_transform (bool) : If exactly one layer has a transform, apply it
            to *all* other layers as well.

    Returns:

        StringIO.StringIO : File-like object containing merge XML document.
    '''
    # Get list of XML layers.
    (width, height), layers = get_svg_layers(svg_sources)

    if share_transform:
        transforms = [layer_i.attrib['transform'] for layer_i in layers
                      if 'transform' in layer_i.attrib]
        if len(transforms) > 1:
            raise ValueError('Transform can only be shared if *exactly one* '
                             'layer has a transform ({} layers have '
                             '`transform` attributes)'.format(len(transforms)))
        elif transforms:
            # Apply single common transform to all layers.
            for layer_i in layers:
                layer_i.attrib['transform'] = transforms[0]

    # Create blank XML output document.
    dwg = svgwrite.Drawing(profile='tiny', debug=False, size=(width, height))

    # Add append layers to output XML root element.
    output_svg_root = etree.fromstring(dwg.tostring())
    output_svg_root.extend(layers)

    # Write merged XML document to output file-like object.
    output = StringIO.StringIO()
    output.write(etree.tostring(output_svg_root))
    output.seek(0)
    return output

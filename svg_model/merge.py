from lxml import etree
import cStringIO as StringIO

import svgwrite

from . import INKSCAPE_NSMAP


def get_svg_layers(svg_sources):
    '''
    Collect layers from input svg sources.

    Args:

        svg_sources (list) : A list of file-like objects, each containing
            one or more XML layers.

    Returns:

        (tuple) : The first item in the tuple is the shape of the largest
            layer, and the second item is a list of `Element` objects (from
            `lxml.etree` module), one per SVG layer.
    '''
    layers = []
    width, height = None, None

    for svg_source_i in svg_sources:
        # Parse input file.
        xml_root = etree.parse(svg_source_i)
        svg_root = xml_root.xpath('/svg:svg', namespaces=INKSCAPE_NSMAP)[0]
        width = max(float(svg_root.attrib['width']), width)
        height = max(float(svg_root.attrib['height']), height)
        layers += svg_root.xpath('//svg:g[@inkscape:groupmode="layer"]',
                                 namespaces=INKSCAPE_NSMAP)

    for i, layer_i in enumerate(layers):
        layer_i.attrib['id'] = 'layer%d' % (i + 1)
    return (width, height), layers


def merge_svg_layers(svg_sources):
    '''
    Merge layers from input svg sources into a single XML document.

    Args:

        svg_sources (list) : A list of file-like objects, each containing
            one or more XML layers.

    Returns:

        (cStringIO.StringIO) : File-like object containing merge XML
            document.
    '''
    # Get list of XML layers.
    (width, height), layers = get_svg_layers(svg_sources)

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

from __future__ import division
from math import atan2, cos, degrees, pi, sin, sqrt
from random import uniform

from pymunk.util import is_clockwise, is_convex
from pymunk import Vec2d


def circle(radius, num_segments):
    verts = []
    for idx in xrange(num_segments):
        theta = 2*pi / num_segments * idx
        verts.append((radius * sin(theta), radius * cos(theta)))
    return verts


def regular(num_faces, first, second):
    if num_faces < 3:
        raise ValueError('num_faces must be >=3')

    internal_angle_deg = 360 / num_faces
    wallvect = Vec2d(second) - Vec2d(first)

    verts = []
    vert = first
    for _ in xrange(num_faces):
        verts.append(vert)
        _vert = (wallvect + vert)
        vert = _vert.x, _vert.y
        wallvect.rotate(-internal_angle_deg)

    return verts


def circle_center(start, face, radius):
    """
    Given two points that lie on the boundary of a circle of given radius,
    return the center of the circle. Of the two possible such circles,
    choose the one on the left of the line from start to (start+face).
    """
    adj_len = sqrt(radius*radius - face.get_length_sqrd() / 4)
    adj = face.perpendicular_normal() * adj_len
    return start + face / 2 - adj



def irregular(start, next, radius, num_verts):
    face = next - start
    center = circle_center(start, face, radius)
    radia = next - center
    theta_max = atan2(radia[1], radia[0])
    end_radia = start - center
    theta_min = atan2(end_radia[1], end_radia[0])
    if theta_min > theta_max:
        theta_min -= 2 * pi

    MIN_DTHETA = (theta_max - theta_min) / num_verts / 4
    theta_min += MIN_DTHETA
    theta_max -= MIN_DTHETA
    thetas = set()
    while len(thetas) < num_verts:
        theta = uniform(theta_min, theta_max)
        if not thetas or min(abs(t - theta) for t in thetas) > MIN_DTHETA:
            thetas.add(theta)
    
    verts = [start, next]
    for theta in sorted(thetas, reverse=True):
        verts.append(center + Vec2d(radius, 0).rotated(degrees(theta)))
    return verts


def assert_valid(verts):
    if len(verts) < 3:
        raise TypeError('need 3 or more verts: %s' % (verts,))
    if not is_convex(verts):
        raise TypeError('not convex: %s' % (verts,))
    if area(verts) == 0.0:
        raise TypeError("colinear: %s" % (verts,))
    # note: pymunk considers y-axis points down, ours points up,
    # hence we consider pymunk's 'clockwise' to be anticlockwise
    if not is_clockwise(verts):
        raise TypeError('anticlockwise winding: %s' % (verts,))


# TODO: obseleted by loop.get_area()
def offset_verts(verts, offset):
    return type(verts)(
        (verts[i][0] + offset[0], verts[i][1] + offset[1])
        for i in range(len(verts))
    )


# TODO: obseleted by loop.get_area()
def area(verts):
    """
    Return area of a simple (ie. non-self-intersecting) polygon.
    Will be negative for counterclockwise winding.
    """
    accum = 0.0
    for i in range(len(verts)):
        j = (i + 1) % len(verts)
        accum += verts[j][0] * verts[i][1] - verts[i][0] * verts[j][1]
    return accum / 2


# TODO: obseleted by loop.get_centroid()
def centroid(verts):
    x, y = 0, 0
    for i in range(len(verts)):
        j = (i + 1) % len(verts)
        factor = verts[j][0] * verts[i][1] - verts[i][0] * verts[j][1]
        x += (verts[i][0] + verts[j][0]) * factor
        y += (verts[i][1] + verts[j][1]) * factor
    polyarea = area(verts)
    x /= 6 * polyarea
    y /= 6 * polyarea
    return (x, y)


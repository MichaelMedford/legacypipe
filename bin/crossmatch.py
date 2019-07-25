#!/usr/bin/env python

# 20 GHz quality control script
#
# Tara Murphy
# 31/01/06
#
# Various routines for crossmatching catalogues
# 

import sys
import re
from math import *
from radec import *

def great_circle_dist1(r1, d1, r2, d2):
    return acos(sin(d1)*sin(d2) + cos(d1)*cos(d2)*cos(r1 - r2))
                                                                                         
def great_circle_dist2(r1, d1, r2, d2):
    return 2 * asin(sqrt(sin((d1 - d2)/2)**2 + cos(d1)*cos(d2)*sin((r1 - r2)/2)**2))
                                                                                         
def precise_dist(ra1, dec1, ra2, dec2):
    d1 = deg2rad(dec1)
    d2 = deg2rad(dec2)
    r1 = deg2rad(ra1)
    r2 = deg2rad(ra2)
    dist = great_circle_dist1(r1, d1, r2, d2)
    dist = rad2deg(dist)
    return dist

def crossmatch(cat1, cat2, radius):
    # radius is in units of degrees
    # finds the best match between given pos from one catalogue and another
    c_zero = 0
    c_one = 0
    matches = []
    nomatch = []

    cat2keys = cat2.keys()
    cat2keys.sort()
    
    for id1 in cat1:
        (cat1rai, cat1deci) = cat1[id1]
        count = 0
        mindiff = 10000
        bestmatch = None
        ramin = cat1rai - (1.1*radius * cos(cat1deci * pi/180.0))
        ramax = cat1rai + (1.1*radius * cos(cat1deci * pi/180.0))

        for id2 in cat2keys:
            (cat2raj, cat2decj) = cat2[id2]
            if cat2raj > ramin and cat2raj < ramax:
                decmin = cat1deci - radius
                decmax = cat1deci + radius

                if cat2decj > decmin and cat2decj < decmax:
                    if cat1deci - cat2decj == 0 and cat1rai - cat2raj == 0:
                        bestmatch = id2
                        mindiff = 0
                    else:
                        diff = precise_dist(cat1rai, cat1deci, cat2raj, cat2decj)
                        if diff < radius:
                            if diff < mindiff:
                                bestmatch = id2
                                mindiff = diff
        if bestmatch:
            matches.append((id1, bestmatch, mindiff))
            c_one += 1
        else:
            nomatch.append(id1)
            c_zero += 1
    return (matches, nomatch)


def countmatch(cat1, cat2, radius):
    # find number of matches within given radius
    # radius is in units of degrees
    c_zero = 0
    c_one = 0
    matches = {}

    cat2keys = cat2.keys()
    cat2keys.sort()

    for id1 in cat1:
        (cat1rai, cat1deci) = cat1[id1]
        ids = []
        count = 0

        for id2 in cat2keys:
            (cat2raj, cat2decj) = cat2[id2]
            if (cat2raj - cat1rai) > 10*radius:
                break
            if (cat1rai - cat2raj) > 10*radius:
                continue
            
            if cat1deci - cat2decj == 0 and cat1rai - cat2raj == 0:
                ids.append(id2)
            else:
                diff = precise_dist(cat1rai, cat1deci, cat2raj, cat2decj)
                if diff < radius:
                    ids.append(id2)
        matches[id1] = ids
    return matches

def crossmatch2(position, cat2, radius):
    #returns sources found in a circle about a given position
    # radius is in units of degrees
    ra_search = position[0]
    dec_search = position[1]
    c_zero = 0
    c_one = 0
    matches = []
    nomatch = []
    
    cat2keys = cat2.keys()
    match = None
    ramin = ra_search - (1.1*radius * cos(dec_search * pi/180.0))
    ramax = ra_search + (1.1*radius * cos(dec_search * pi/180.0))
    print(ramin, ramax)
    print(ra_search, dec_search)
    for id2 in cat2keys:
        (cat2ra, cat2dec) = cat2[id2]
        if cat2ra > ramin and cat2ra < ramax:
            decmin = dec_search - radius
            decmax = dec_search + radius
            diff = precise_dist(ra_search, dec_search, cat2ra, cat2dec)
            if cat2dec > decmin and cat2dec < decmax:
                if diff < radius:
                    #print 'MATCH:', id2, cat2[id2], diff
                    matches.append((id2, diff))
            else:
                nomatch.append(id2)
    return matches, nomatch

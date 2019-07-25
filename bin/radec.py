#!/usr/bin/env python

# 20 GHz quality control script
#
# Tara Murphy
# 31/01/06
#
# Various routines for dealing with RA/Dec conversions
# 


from math import pi
from math import floor

def ra2dec(ra):
  r = ra.split(':')
  if len(r) == 2:
    r.append(0.0)
  return (float(r[0]) + float(r[1])/60.0 + float(r[2])/3600.0)*15

def dec2dec(dec):
  d = dec.split(':')
  if len(d) == 2:
    d.append(0.0)
  if d[0].startswith('-') or float(d[0]) < 0:
    return float(d[0]) - float(d[1])/60.0 - float(d[2])/3600.0
  else:
    return float(d[0]) + float(d[1])/60.0 + float(d[2])/3600.0

def ra2str(ra):
  ra = ra/15.0
  hh = int(ra)
  diff = ra - hh
  mm = int(diff*60)
  diff = diff - (mm/60.0)
  ss = diff*3600
  if ss >= 59.995:
    ss = 0
    mm += 1

  str = '%02d:%02d:%05.2f' % (hh, mm, ss)
  return str

def dec2str(dec):
  neg = 0
  if dec < 0:
    dec *= -1
    neg = 1
  dd = int(dec)
  diff = dec - dd
  mm = int(diff*60)
  diff = diff - (mm/60.0)
  ss = diff*3600
  if ss >= 59.995:
    ss = 00.0
    mm += 1

  if neg:
    str = '-%02d:%02d:%05.2f' % (dd, mm, ss)
  else:
    str = '%02d:%02d:%05.2f' % (dd, mm, ss)
  return str


def rad2deg(x):
    return x * 180.0 / pi

def deg2rad(x):
    return x * pi / 180.0

# main program
#str = '10:11:13.54'
#print str
#ra = ra2dec(str)
#ra2str(ra)

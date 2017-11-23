# -*- coding: utf-8 -*-

# maps_polygons.py - (C) 2017 Martin Schorb EMBL
#
# takes a SerialEM navigator and generates virtual maps from a given low-mag map at the posisiton of detected features
# 
# input:
# - the file name of the navigator (overview maps acquisition-labeled)
# - the navigator label of a map acquired in the target conditions (will be cloned for the virtual maps)
#
# output:
# - one tif file at the desired virtual magnification and image size for each item
# - a new navigator file containing all new maps/items with acquisition already enabled

# dependencies


import numpy
import tifffile as tiff
import emtools as em


# PARAMETERS


navname = 'test1.nav'
# file name navigator


target_map = 'refmap'
# one example map at the desired settings (NavLabel)

c = [664, 1548]

p = numpy.array(#[522, 616])
[[  720. , 1568.],
 [  688. , 1600.],
 [  664. , 1620.],
 [  632. , 1604.],
 [  616. , 1600.],
 [  600. , 1588.],
 [  584. , 1568.],
 [  572. , 1532.],
 [  600. , 1508.],
 [  632. , 1496.],
 [  680. , 1488.],
 [  760. , 1496.],
 [  720. , 1568.]])

navlines = em.loadtext(navname)
curr_map = em.nav_item(navlines,'2')

targetitem = em.nav_item(navlines,target_map)


# rotmat = curr_map['rotmat']

nav=list()

newnav = navname[:-4] + '_automaps.nav'
nnf = open(newnav,'w')
nnf.write("%s\n" % navlines[0])
nnf.write("%s\n" % navlines[1])

# im = curr_map['im']
# ====================================================================================

mapfile = em.map_file(curr_map)
mergefile = mapfile[:mapfile.rfind('.mrc')]  

mergefile = mergefile + '_merged.tif'
im = tiff.imread(mergefile)

outnav = em.pts2nav(im,p,c,curr_map,targetitem,nav)

for nitem in outnav:
 
  out = em.itemtonav(nitem,nitem['# Item'])
  for item in out: nnf.write("%s\n" % item)

            
nnf.close()

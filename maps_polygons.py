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

reload(em)

# PARAMETERS


navname = 'test1.nav'
# file name navigator


target_map = 'refmap'
# one example map at the desired settings (NavLabel)

c = [[376, 1712]]

p = [numpy.array([[  444.,  1720.],
       [  428.,  1756.],
       [  404.,  1784.],
       [  360.,  1784.],
       [  332.,  1772.],
       [  320.,  1744.],
       [  304.,  1720.],
       [  292.,  1680.],
       [  324.,  1656.],
       [  360.,  1644.],
       [  392.,  1664.],
       [  416.,  1688.],
       [  444.,  1720.]])]



navlines = em.loadtext(navname)
curr_map = em.nav_item(navlines,'2')

targetitem = em.nav_item(navlines,target_map)


allitems = em.fullnav(navlines)
# rotmat = curr_map['rotmat']

nav=allitems

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

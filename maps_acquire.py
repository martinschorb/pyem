# -*- coding: utf-8 -*-

# maps_acquire.py - (C) 2017 Martin Schorb EMBL
#
# takes a SerialEM navigator and generates virtual maps from a given low-mag map at the posisiton of selected points
# 
# input:
# - the file name of the navigator
#  - the navigator label of a map acquired in the target conditions (will be cloned for the virtual maps)
#
# output:
# - one tif file at the desired virtual magnification and image size for each item
# - a new navigator file containing all new maps with acquisition already enabled



# PARAMETERS


navname = 'test1.nav'
# file name navigator


target_map = 'refmap'
# one example map at the desired settings (NavLabel)



# ====================================================================================


# dependencies

import fnmatch
import os
import os.path
import sys
import time
import numpy
import scipy
import math
import matplotlib.pyplot as plt
import re
from scipy.ndimage.interpolation import zoom
import tifffile as tiff

import emtools as em



# -------------------------------


# -------------------------------



# -------------------------------




# -------------------------------





# start script


navlines = em.loadtext(navname)
targetitem = em.nav_item(navlines,target_map)

targetfile = em.map_file(targetitem)
targetheader = em.map_header(targetfile)


newnav = navname[:-4] + '_automaps.nav'
nnf = open(newnav,'w')
nnf.write("%s\n" % navlines[0])
nnf.write("%s\n" % navlines[1])


allitems = em.fullnav(navlines)



acq = filter(lambda item:item.get('Acquire'),allitems)
acq = filter(lambda item:item['Acquire']==['1'],acq)

non_acq = [x for x in allitems if x not in acq]

    
for item in non_acq:
  out = em.itemtonav(item,item['# Item'])
  for line in out: nnf.write("%s\n" % line)


maps = {}

newmapid = 1000

outnav=list()

for acq_item in acq:
  newmapid = newmapid + 1
  mapitem = em.realign_map(acq_item,allitems)
  
  itemid = mapitem['# Item']
  
  if not itemid in maps.keys():
    maps[itemid] = em.mergemap(mapitem)

  ptitem = acq_item
      
  xval = (float(ptitem['PtsX'][0]))
  yval = (float(ptitem['PtsY'][0]))
  
  pt = numpy.array([xval,yval])

  tilepos = maps[itemid]['tilepos']
  
  if len(tilepos.shape)<2:
    tileid = 0
  else:
    tiledist = numpy.sum((tilepos-pt)**2,axis=1)
    tileid = numpy.argmin(tiledist)
  
  
  # normalize coordinates
  
  ptn = numpy.matrix(pt - tilepos[tileid])

  # calculate the pixel coordinates
  
  pt_px = numpy.array(ptn * numpy.transpose(maps[itemid]['rotmat']) / maps[itemid]['mapheader']['pixelsize'] + maps[itemid]['mappxcenter'])
  pt_px = pt_px.squeeze()
  pt_px1 = pt_px + maps[itemid]['tilepx'][tileid]
  pt_px1[1] = maps[itemid]['mergeheader']['ysize'] - pt_px1[1]
  
	    
  
  px_scale = targetheader['pixelsize'] /( maps[itemid]['mapheader']['pixelsize'] )

  imsz1 = numpy.array([targetheader['xsize'],targetheader['ysize']]) * px_scale

  px = round(pt_px1[0])
  py = round(pt_px1[1])
  
  if px < 0 or py < 0:
    print 'Warning! Item ' + acq_item['# Item'] + ' is not within the map frame. Ignoring it'
  else:

    xel = range(int(px - imsz1[0]/2) , int(px + round(float(imsz1[0])/2)))
    yel = range(int(py - imsz1[1]/2) , int(py + round(float(imsz1[1])/2)))
    
    im = maps[itemid]['im']
    
    imsize = numpy.array(im.shape)
    
    im1=im[yel,:]

    im1=im1[:,xel]
  #            %matplotlib inline
	      


  #    print(points[i])
    im2 = zoom(im1,1/px_scale)
    
    imsize2 = im2.shape
    #plt.imshow(im2)

    imfile = 'virt_map_' + acq_item['# Item'] + '.tif'
	    
    tiff.imsave(imfile,im2)
    
    cx = imsize2[1]
    cy = imsize2[0]

    a = [[0,0],[cx,0],[cx,cy],[0,cy],[0,0]]
    a = numpy.matrix(a) - [cx/2 , cy/2]
    
    c1 = a*maps[itemid]['rotmat'] * targetheader['pixelsize'] + pt
    
    cnx = numpy.array(numpy.transpose(c1[:,1]))
    cnx = numpy.array2string(cnx,separator=' ')
    cnx = cnx[2:-2]
    
    cny = numpy.array(numpy.transpose(c1[:,0]))
    cny = " ".join(map(str,cny))
    cny = cny[1:-2]
    
    
    
    
  # fill navigator
  
    acq_item['Acquire'] = '0'
    
    outnav.append(acq_item)
    
    
    newnavitem = dict(targetitem)
    
    newnavitem['MapFile'] = [imfile]
    newnavitem['StageXYZ'] = ptitem['StageXYZ']
    newnavitem['RawStageXY'] = ptitem['StageXYZ'][0:2]
    newnavitem['PtsY'] = cnx.split()
    newnavitem['PtsX'] = cny.split()
    newnavitem['NumPts'] = ['1']
    newnavitem['Note'] = newnavitem['MapFile']
    newnavitem['MapID'] = [str(newmapid)]
    newnavitem['Acquire'] = ['1']
    newnavitem['MapSection'] = ['0']
    newnavitem['SamePosId'] = acq_item['MapID']
    # newnavitem['MapWidthHeight'] = [str(im2size[0]),str(im2size[1])]
    newnavitem['ImageType'] = ['2']
    newnavitem['MapMinMaxScale'] = [str(numpy.min(im2)),str(numpy.max(im2))]
    newnavitem['NumPts'] = ['5']
    newnavitem['# Item'] = 'map_' + acq_item['# Item']    
    
    outnav.append(newnavitem)
    
    outnav.sort()
   
for nitem in outnav:
 
  out = em.itemtonav(nitem,nitem['# Item'])
  for item in out: nnf.write("%s\n" % item)

            
nnf.close()

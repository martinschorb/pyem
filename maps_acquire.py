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


navname = 'navwim.nav'
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
#import matplotlib.pyplot as plt
import re
from scipy.ndimage.interpolation import zoom
import tifffile as tiff
import mrcfile as mrc

import emtools as em

reload(em)


# start script


navlines = em.loadtext(navname)
targetitem = em.nav_item(navlines,target_map)

targetfile = em.map_file(targetitem)
target_mrc = mrc.open(targetfile, permissive = 'True')
targetheader = em.map_header(target_mrc)

tx = map(float,targetitem['PtsX'])
ty = map(float,targetitem['PtsY'])

targetrot = em.map_rotation(tx,ty)

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
ntotal = len(acq)

for idx,acq_item in enumerate(acq):
  print('Processing navitem '+ str(idx+1) + '/' + str(ntotal) + ' (%2.0f%% done)' %(idx*100/ntotal))

  newmapid = em.newmapID(allitems,newmapid + 1)
  mapitem = em.realign_map(acq_item,allitems)
  
  itemid = mapitem['# Item']
    
  if not itemid in maps.keys():
    maps[itemid] = em.mergemap(mapitem)
    
    
  mx = map(float,mapitem['PtsX'])
  my = map(float,mapitem['PtsY'])

  rotmat = em.map_rotation(mx,my)
  # combine rotation matrices
  rotm1 = rotmat.T * targetrot  
  xval = (float(acq_item['PtsX'][0]))
  yval = (float(acq_item['PtsY'][0]))
  
  pt = numpy.array([xval,yval])
  
  # calculate the pixel coordinates
  im = maps[itemid]['im'] 
  
  imsz = im.shape
  
  tileloc= maps[itemid]['tileloc']
  
  
  if 'XYinPc' in acq_item:
    tileid = int(acq_item['PieceOn'][0])
    pt_px0 = map(float,acq_item['XYinPc'])
    pt_px = numpy.array(pt_px0)
    #pt_px[0] = maps[itemid]['mapheader']['xsize'] - pt_px[0]
    #pt_px[1] = pt_px[1]   
    
    
  else:
         
    tilepos = maps[itemid]['tilepos']
    if numpy.diff(tilepos,axis=0)[0].max() == 0:
      print('Montage created using image shift! Problems in identifying the positions of clicked points accurately possible!')
	  
    if len(tilepos.shape)<2:
      tileid = 0
    else:
      tiledist = numpy.sum((tilepos-pt)**2,axis=1)
      tileid = numpy.argmin(tiledist)
    
    
    # normalize coordinates
    
    ptn = numpy.matrix(pt - tilepos[tileid])
    pt_px = numpy.array(ptn * numpy.transpose(maps[itemid]['rotmat']) / maps[itemid]['mapheader']['pixelsize'] + maps[itemid]['mappxcenter'])
    pt_px = pt_px.squeeze()



  
  
  pt_px1 = pt_px + maps[itemid]['tilepx'][tileid]
  pt_px1[1] = imsz[0] - pt_px1[1]
  	    
  
  px_scale = targetheader['pixelsize'] /( maps[itemid]['mapheader']['pixelsize'] )

  imsz1 = numpy.array([targetheader['xsize'],targetheader['ysize']]) * px_scale 
     
  im2, p2 = em.map_extract(im,pt_px1,pt_px1,px_scale,imsz1,rotm1)


  #px = round(pt_px1[0])
  #py = round(pt_px1[1])
  
  if min(im2.shape)<200:
    print('Warning! Item ' + acq_item['# Item'] + ' is not within the map frame. Ignoring it')
  else:

    #xel = range(int(px - imsz1[0]/2) , int(px + round(float(imsz1[0])/2)))
    #yel = range(int(py - imsz1[1]/2) , int(py + round(float(imsz1[1])/2)))
    
    #im = maps[itemid]['im']
    
    #imsize = numpy.array(im.shape)
    
    #im1=im[yel,:]

    #im1=im1[:,xel]
	      


  #    print(points[i])
    #im2 = zoom(im1,1/px_scale)

    imsize2 = im2.shape
    #plt.imshow(im2)

    imfile = 'virt_map_' + acq_item['# Item'] + '.tif'
    
    if os.path.exists(imfile): os.remove(imfile)
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
    newnavitem['StageXYZ'] = acq_item['StageXYZ']
    newnavitem['RawStageXY'] = acq_item['StageXYZ'][0:2]
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

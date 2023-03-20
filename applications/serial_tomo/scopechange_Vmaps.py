# -*- coding: utf-8 -*-

# maps_acquire.py - (C) 2018 Martin Schorb EMBL
#
# takes a SerialEM navigator and generates virtual maps from a given low-mag map at the posisiton of selected points
# 
# input:
# - the file name of the navigator
#  - the navigator label of a map acquired in the target conditions (will be cloned for the virtual maps)
#
# output:
# - one mrc file at the desired virtual magnification and image size for each item
# - a new navigator file containing all new maps with acquisition already enabled



# PARAMETERS


import sys
import os

navname = sys.argv[1]
# file name navigator

# change path to working directory
os.chdir(os.path.dirname(navname))




target_map = 'refmap'
# one example map at the desired settings (NavLabel)


# ====================================================================================


# dependencies

import os
import os.path
import numpy
from operator import itemgetter

#import matplotlib.pyplot as plt

#import tifffile as tiff
import mrcfile as mrc
import pyEM as em


# start script


navlines = em.loadtext(navname)
(targetitem,junk) = em.nav_item(navlines,target_map)

targetfile = em.map_file(targetitem)
target_mrc = mrc.open(targetfile, permissive = 'True')
targetheader = em.map_header(target_mrc)

t_mat = em.map_matrix(targetitem)

allitems = em.fullnav(navlines)

newnavf = navname[:-4]+'_updated.nav'
nnf = open(newnavf,'w')
nnf.write("%s\n" % navlines[0])
nnf.write("%s\n" % navlines[1])

acq = em.nav_selection(allitems)
ntotal = len(acq)
idx=0;

for acq_item in allitems:
  
  if  acq_item.get('Acquire') == ['1']:
      print('Processing navitem '+ str(idx+1) + '/' + str(ntotal) + ' (%2.0f%% done)' %(idx*100/ntotal))
      idx = idx+1
      mapitem = acq_item
      
      itemid = mapitem['# Item']
        
      thismap = em.mergemap(mapitem)   
    
      # combine rotation matrices
      
      map_mat = thismap['matrix'] 
      
      maptf = (numpy.linalg.inv(map_mat) * t_mat).T  
      
      xval = float(acq_item['StageXYZ'][0]) #(float(acq_item['PtsX'][0]))
      yval = float(acq_item['StageXYZ'][1]) #(float(acq_item['PtsY'][0]))
      
      pt = numpy.array([xval,yval])
      
      # calculate the pixel coordinates
    
     
    
      px_scale = targetheader['pixelsize'] /( thismap['mapheader']['pixelsize'] )
    
      imsz1 = numpy.array([targetheader['ysize'],targetheader['xsize']])
      pt_px1 = imsz1/2
      
      im = numpy.array(thismap['im'])
    
      im2, p2 = em.map_extract(im,pt_px1,pt_px1,px_scale,imsz1,maptf)
      
      im2[im2==0] = int(numpy.mean(im2[im2>0]))
    
      if min(im2.shape)<200:
        print('Warning! Item ' + acq_item['# Item'] + ' is not within the map frame. Ignoring it')
      else:
    
        # pad item numbers to 4 digits    
 #       if acq_item['# Item'].isdigit(): acq_item['# Item'] = acq_item['# Item'].zfill(4)
                    
        imfile = 'virt_map_' + acq_item['# Item'] + '.mrc'
        
        if os.path.exists(imfile): os.remove(imfile)
    #    tiff.imsave(imfile,im2)
        
        im2 = numpy.rot90(im2,3)
    
        with mrc.new(imfile) as mrcf:
            mrcf.set_data(im2.T)
            mrcf.close()#        

    
        # fill navigator
    
        acq_item['Acquire'] = '0'
        
        # NoRealign
        # acq_item['Color'] = '5'       
               
             
        cx = im2.shape[0]
        cy = im2.shape[1]
    
        a = [[0,0],[cx,0],[cx,cy],[0,cy],[0,0]]
        a = numpy.matrix(a) - [cx/2 , cy/2]
        
        t_mat_i = numpy.linalg.inv(t_mat)
    
        c1 = a*t_mat_i.T + pt
    
        cnx = numpy.array(numpy.transpose(c1[:,1]))
        cnx = numpy.array2string(cnx,separator=' ')
        cnx = cnx[2:-2]
    
        cny = numpy.array(numpy.transpose(c1[:,0]))
        cny = " ".join(list(map(str,cny)))
        cny = cny[1:-2]

  


        acq_item['MapScaleMat'] = targetitem['MapScaleMat']
        acq_item['MapBinning'] = targetitem['MapBinning']
        acq_item['MapSpotSize'] = targetitem['MapSpotSize']
        acq_item['MapMagInd'] = targetitem['MapMagInd']
        acq_item['MapIntensity'] = targetitem['MapIntensity']
        acq_item['MapCamera'] = targetitem['MapCamera']
        acq_item['MapExposure'] = targetitem['MapExposure']
        acq_item['MapSection'] = '0'
        acq_item['PtsY'] = cnx.split()
        acq_item['PtsX'] = cny.split()      
    
    
        acq_item['MapFile'] = [imfile]
        
        acq_item['Note'] = acq_item['MapFile']
        acq_item['ImageType'] = ['0']
        acq_item['MapMinMaxScale'] = [str(numpy.min(im2)),str(numpy.max(im2))]
        

for nitem in allitems: 
    out = em.itemtonav(nitem,nitem['# Item'])
    for item in out: nnf.write("%s\n" % item)
            
    

nnf.close()

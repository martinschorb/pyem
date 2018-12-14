# -*- coding: utf-8 -*-

# maps_reg.py - (C) 2018 Martin Schorb EMBL
#
# takes a SerialEM navigator and 
# 
# input:
# - the file name of the navigator
#  
#
# output:
# 


# PARAMETERS


navname = 'nav2.nav'
# file name navigator





# ====================================================================================


# dependencies


import pyEM as em
import numpy
import os
import tifffile as tiff
from skimage import transform as tf


# start script


navlines = em.loadtext(navname)
allitems = em.fullnav(navlines)


# Find all Registration Points
regpts = filter(lambda item:item.get('RegPt'),allitems)


# Find all Maps to process
acq = filter(lambda item:item.get('Acquire'),allitems)
acq = list(filter(lambda item:item['Acquire']==['1'],acq))



regidx = []
regreg = []
regmap = []

for regpoint in regpts:
    regidx.append(int(regpoint['RegPt'][0]))
    regreg.append(int(regpoint['Regis'][0]))
    regmap.append(regpoint['DrawnID'][0])
    
regidx = numpy.array(regidx)
regreg = numpy.array(regreg)
regmap = numpy.array(regmap)


# Process each map
for mapitem in acq:
    
    start_map = em.mergemap(mapitem)
    
    # find the Registration Points on this Map
    mapregpt_idx = numpy.where(regmap==mapitem['MapID'])[0]
    mapregpt_ptidx = regidx[mapregpt_idx]
    
    mapreg = mapitem['Regis']
    
    # find maps in the same Registratoin that will be transformed as well
    sameregmaps = filter(lambda item:item.get('MapMontage'),allitems)
    sameregmaps = filter(lambda item:item['Regis']==mapreg,sameregmaps)
    sameregmaps = list(filter(lambda item:item['MapWidthHeight']==mapitem['MapWidthHeight'],sameregmaps))
    
#    sameregmaps.remove(mapitem)
    
    mapreg = int(mapreg[0])
    
    em_pt = []   
    lm_pt = []
    
    
    # find the corresponding registration point pairs and target map
    pair0 = numpy.where(regidx==regidx[mapregpt_idx[0]])[0]
    
    # determine correct order for this pair
    if regreg[pair0[0]]==mapreg:
        pair0 =  numpy.array([pair0[1],pair0[0]])
        
    
    reg_start = regreg[pair0[1]]
    reg_target = regreg[pair0[0]]
    
    targetitem = regpts[pair0[0]]
    target_mitem = list(filter(lambda item:item['MapID']==targetitem['DrawnID'],allitems))[0]
    target_map = em.mergemap(target_mitem)
    
     
    # determine pixel coordinates for each registration point for this map's transform   
    for index in mapregpt_idx:
        pair = numpy.where(regidx==regidx[index])[0]
        
        # determine correct order for this pair
        if regreg[pair[0]]==mapreg:
            pair =  numpy.array([pair[1],pair[0]])
            
        targetitem = regpts[pair[0]]
        startitem = regpts[pair[1]]
        
        em_pt.append(em.get_mergepixel(targetitem,target_map))
        lm_pt.append(em.get_mergepixel(startitem,start_map))
        
    lm_pt1 = numpy.squeeze(lm_pt)
    em_pt1 = numpy.squeeze(em_pt)
    
    
    # generate Transformation
    tform = tf.SimilarityTransform()
    tform.estimate(em_pt1,lm_pt1)
    
    # Transform and export all maps in this Registration
    for tfmmap in sameregmaps:
        srcmap = em.mergemap(tfmmap)
        warped = tf.warp(numpy.array(srcmap['im']), tform, output_shape = target_map['im'].shape)
        
        if warped.dtype == 'float': 
            if srcmap['im'].dtype == 'uint8':
                warped = (warped*255)
            elif srcmap['im'].dtype == 'uint16':
                warped = (warped*65535)
                    
            warped = warped.astype(srcmap['im'].dtype)
        
        # file names and export
        startname = os.path.splitext(os.path.basename(srcmap['mapfile']))[0]
        targetname = os.path.splitext(os.path.basename(target_map['mergefile']))[0]
        outfile = startname+'->'+targetname+'.tif'
        tiff.imsave(outfile,warped)

    
        
    
    
    

    
    
    
    
    

   
            
            
            
            
        
    
    
        
    
    
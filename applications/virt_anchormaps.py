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
# - one tif file at the desired virtual magnification and image size for each item
# - a new navigator file containing all new maps with acquisition already enabled



# PARAMETERS


import sys
import os

navname = sys.argv[1]
# file name navigator

# change path to working directory
os.chdir(os.path.dirname(navname))


navname = sys.argv[1]
# file name navigator


view_map = 'view'#map'
# one example map at the desired settings (View) (NavLabel)

preview_map = 'preview'#map'
# one example map at the desired settings (Preview) (NavLabel)


# ====================================================================================
#%%


# dependencies

import os
import os.path
import numpy

#import matplotlib.pyplot as plt

#import tifffile as tiff
import mrcfile as mrc
import pyEM as em

# loop function
def virtmapfrompoint(acq_item,idx,allitems,maps,targetitem,target_merge,resultlist):
      
      newnav = list()
      #targetfile = em.map_file(targetitem)
      #target_mrc = mrc.open(targetfile, permissive = 'True')
      #targetheader = em.map_header(target_mrc)
      
      #target_merge = em.mergemap(targetitem)
      targetheader = target_merge['mergeheader']
    
      t_mat = em.map_matrix(targetitem)

      delim = 100000
      newmapid = em.newID(allitems,divmod(int(targetitem['MapID'][0]),delim)[0]*delim + idx * 100)
      mapitem = em.realign_map(acq_item,allitems)
      
      itemid = mapitem['# Item']
        
      if not itemid in maps.keys():
        maps[itemid] = em.mergemap(mapitem)
        groupid = [str(em.newID(allitems,999000000+int(mapitem['MapID'][0][-6:])))]
        non_acq.remove(mapitem)
        print('add original map to navigator')
        # NoRealign
        mapitem['Color'] = '5'            
        maps['mapnav'].append(mapitem)
        
      else:
        groupid = resultlist[-1]['GroupID']
        
    
      # combine rotation matrices
      
      map_mat = maps[itemid]['matrix'] 
      
      maptf = (numpy.linalg.inv(map_mat) * t_mat).T  
      
      xval = float(acq_item['StageXYZ'][0]) #(float(acq_item['PtsX'][0]))
      yval = float(acq_item['StageXYZ'][1]) #(float(acq_item['PtsY'][0]))
      
      pt = numpy.array([xval,yval])
      
      # calculate the pixel coordinates
    
      pt_px1 = em.get_pixel(acq_item,maps[itemid])
    
      px_scale = targetheader['pixelsize'] /( maps[itemid]['mapheader']['pixelsize'] )
    
      imsz1 = numpy.array([targetheader['ysize'],targetheader['xsize']])
      
      im = numpy.array(maps[itemid]['im'])
    
      im2, p2 = em.map_extract(im,pt_px1,pt_px1,px_scale,imsz1,maptf)
      
      im2size = im2.shape
    
      if min(im2.shape)<200:
        print('Warning! Item ' + acq_item['# Item'] + ' is not within the map frame. Ignoring it')
      else:
    
        # pad item numbers to 4 digits    
        if acq_item['# Item'].isdigit(): acq_item['# Item'] = acq_item['# Item'].zfill(4)
                    
        newnavitem = dict(targetitem)
            
        if 'MapLDConSet' in targetitem.keys():
            newnavitem['MapLDConSet'] = targetitem['MapLDConSet']
            newmapid = newmapid + int(targetitem['MapLDConSet'][0])
            if targetitem['MapLDConSet'] == ['0']:
                prefix = 'V_'
                newnavitem['Acquire'] = ['0']
            elif targetitem['MapLDConSet'] == ['4']:
                #newnavitem['Acquire'] = ['1']
                prefix = 'P_'
            else:
                prefix='m_'
                newnavitem['Acquire'] = ['1']
        else:
            prefix=''
                    
        imfile = prefix + acq_item['# Item'] + '.mrc'
        
        if os.path.exists(imfile): os.remove(imfile)
    #    tiff.imsave(imfile,im2)
        
        im3 = numpy.rot90(im2,3)
    
        with mrc.new(imfile) as mrcf:
            mrcf.set_data(im3.T)
            mrcf.close()#        
            
        cx = im2.shape[1]
        cy = im2.shape[0]
    
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
    
    
        # fill navigator
    
        acq_item['Acquire'] = '0'
        
        # NoRealign
        # acq_item['Color'] = '5'
        
        newnavitem['MapFile'] = [imfile]
        newnavitem['StageXYZ'] = acq_item['StageXYZ']
        newnavitem['RawStageXY'] = acq_item['StageXYZ'][0:2]
        newnavitem['PtsY'] = cnx.split()
        newnavitem['PtsX'] = cny.split()
        newnavitem['NumPts'] = ['1']
        newnavitem['Note'] = newnavitem['MapFile']
        newnavitem['MapID'] = [str(newmapid)]
        newnavitem['MapSection'] = ['0']
        newnavitem['SamePosId'] = acq_item['MapID']
        newnavitem['GroupID'] = groupid
        newnavitem['MapWidthHeight'] = [str(im2size[1]),str(im2size[0])]
        newnavitem['ImageType'] = ['0']
        newnavitem['MapMinMaxScale'] = [str(numpy.min(im2)),str(numpy.max(im2))]
        newnavitem['NumPts'] = ['5']
        newnavitem['# Item'] = prefix + acq_item['# Item']    
    
        newnav.append(newnavitem)     
        
        return newnav.copy(),maps




# start script


navlines = em.loadtext(navname)
(targetitem,junk) = em.nav_item(navlines,view_map)


newnavf = navname[:-4] + '_automaps.nav'
nnf = open(newnavf,'w')
nnf.write("%s\n" % navlines[0])
nnf.write("%s\n\n" % navlines[1])


allitems = em.fullnav(navlines)


acq = filter(lambda item:item.get('Acquire'),allitems)
acq = list(filter(lambda item:item['Acquire']==['1'],acq))

non_acq = [x for x in allitems if x not in acq]

non_acq.remove(targetitem)
    
maps = {}
maps['mapnav'] = []

newmapid = em.newID(allitems,10000)

outnav1=list()
ntotal = len(acq)

(viewitem,junk) = em.nav_item(navlines,view_map)
(previewitem,junk) = em.nav_item(navlines,preview_map)

view_merge = em.mergemap(viewitem)
preview_merge = em.mergemap(previewitem)

#-----
#%%



for idx,acq_item in enumerate(acq):
  print('Processing navitem '+ str(idx+1) + '/' + str(ntotal) + ' (%2.0f%% done)' %(idx*100/ntotal))  
  (viewnav,maps) = virtmapfrompoint(acq_item,idx,allitems,maps,viewitem,view_merge,outnav1.copy())
  outnav1.append(acq_item)
  outnav1.extend(viewnav.copy())  
  (previewnav,maps) = virtmapfrompoint(acq_item,idx,allitems,maps,previewitem,preview_merge,outnav1.copy())
  outnav1.extend(previewnav)
  


#finalnav.sort(key=itemgetter('# Item'))
on1=em.ordernav(outnav1, delim='_')

finalnav = maps['mapnav'].copy()
finalnav.extend(on1.copy())
  
   
for nitem in finalnav: 
  out = em.itemtonav(nitem,nitem['# Item'])
  for item in out: nnf.write("%s\n" % item)

            
nnf.close()

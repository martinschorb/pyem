# -*- coding: utf-8 -*-
# import the py-EM module and make its functions available
import pyEM as em
import numpy as np
from skimage import filters
from scipy import ndimage
from scipy.ndimage.morphology import binary_fill_holes
# parse command line parameters

#import argparse

#parser = argparse.ArgumentParser(description='Sort navigator file.')
#parser.add_argument('navfile', metavar='navfile', type=str, help='a navigator file location')

#args = parser.parse_args()

#navfile = args.navfile


#relative size of the biggest cell/object in the image
relsize = 0.8

#%%

import sys

navfile = sys.argv[1]

#%%

# load the navigator file
navlines = em.loadtext(navfile)
allitems = em.fullnav(navlines)



acq = em.nav_selection(allitems)

for item in acq:
    if not item['Type'] == ['2']:
        print("Skipping item "+item['# Item']+" - not a map.")
        continue
    
    print("Adding polygons to map "+item['# Item']+'.')
    
    merge = em.mergemap(item)
    
    im = merge['im']
    g1 = filters.gaussian(im,sigma=13)
    val = filters.threshold_otsu(g1)    
    imsz = np.array([merge['mergeheader']['xsize'],merge['mergeheader']['ysize']])
    c = (imsz/2).astype(int)
    
    distim0 = g1<val
    distim = distim0.copy()
    distim0 = binary_fill_holes(distim0)
    
    if g1[c[0],c[1]]>val:
        #cell is not in the center, find biggest one
        distim = distim.copy()
        
        # exclude edge cells
        distim[:int((1-relsize)/2*imsz[0]),:]=False
        distim[-int((1-relsize)/2*imsz[0]):,:]=False
        
        distim[:,:int((1-relsize)/2*imsz[1])]=False
        distim[:,-int((1-relsize)/2*imsz[1]):]=False
        
        
        
        distance = ndimage.distance_transform_edt(distim)
        c_n = np.divmod(np.argmax(distance),imsz[0])
        c = np.array([c_n[1],c_n[0]])   
    

    
    pts = em.img2polygon(distim0,17, c, int(imsz.max()*relsize))
        
    
    allitems.extend(em.ptsonmap(item,[pts],allitems))
    

# create new file by copying the header of the input file
newnavf = navfile[:-4] + '_polygons.nav'

print('Polygons were created and output is written as: ' + newnavf)

em.write_navfile(newnavf,allitems,xml=False)
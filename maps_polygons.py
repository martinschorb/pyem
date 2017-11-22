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
#import matplotlib.pyplot as plt
from scipy.ndimage.interpolation import zoom
from scipy.ndimage import rotate

import tifffile as tiff
import math
import emtools as em


# PARAMETERS


navname = 'test2.nav'
# file name navigator


target_map = 'refmap'
# one example map at the desired settings (NavLabel)

binning = 4

c = [4444, 648]


p = numpy.array([[ 4484. ,  642.],
 [ 4472. ,  660.],
 [ 4464. ,  682.],
 [ 4438. ,  684.],
 [ 4422.,   668.],
 [ 4412.  , 652.],
 [ 4410.  , 632.],
 [ 4416.  , 610.],
 [ 4440.  , 606.],
 [ 4454.  , 620.],
 [ 4468.  , 626.],
 [ 4484.  , 642.]])

navlines = em.loadtext(navname)
curr_map = em.nav_item(navlines,'1')

index = 1
mapid = 1001
pixelsize = 0.005186


mx = map(float,curr_map['PtsX'])
my = map(float,curr_map['PtsY'])

rotmat = em.map_rotation(mx,my)

# rotmat = curr_map['rotmat']
mergefile = 'map2_merged.tif'

im = tiff.imread(mergefile)
# im = curr_map['im']
# ====================================================================================
outnav=list()

newnav = navname[:-4] + '_automaps.nav'
nnf = open(newnav,'w')
nnf.write("%s\n" % navlines[0])
nnf.write("%s\n" % navlines[1])

# inititate script

targetitem = em.nav_item(navlines,target_map)
targetfile = em.map_file(targetitem)
targetheader = em.map_header(targetfile)

tx = map(float,targetitem['PtsX'])
ty = map(float,targetitem['PtsY'])
  
targetrot = em.map_rotation(tx,ty)


allitems = em.fullnav(navlines)

 
px_scale = targetheader['pixelsize'] /pixelsize

imsz = numpy.array(im.shape)

imsz1 = numpy.array([targetheader['xsize'],targetheader['ysize']]) * px_scale



px = round(c[0])
py = round(c[1])



# extract image (1.42x to enable rotation)

xel = range(int(px - 1.42 * imsz1[0]/2) , int(px + 1.42 * round(float(imsz1[0])/2)))
yel = range(int(py - 1.42 * imsz1[1]/2) , int(py + 1.42 * round(float(imsz1[1])/2)))

im1=im[yel,:]
im1=im1[:,xel]

# center to origin
p1 = p - c

#c[1] = imsz[1] - c[1]

# combine rotation matrices
rotm1 = rotmat.T * targetrot
angle = math.degrees(math.acos(rotm1[0,0]))

# interpolate image
im2 = zoom(im1,1/px_scale)

p2 = p1/px_scale

# rotate
im3 = rotate(im2,angle)
p3 =  p2 * rotm1.T

t_size = imsz1/px_scale
c3 = numpy.array(im3.shape)/2


#crop to desired size

xel3 = range(int(c3[0] - t_size[0]/2) , int(c3[0] + round(float(t_size[0])/2)))
yel3 = range(int(c3[1] - t_size[1]/2) , int(c3[1] + round(float(t_size[1])/2)))

im4 = im3[yel3,:]
im4 = im4[:,xel3]

p4 = p3
p4[:,0] = p3[:,0] + t_size[0]/2
p4[:,1] = t_size[1]/2 - p3[:,1]

label = curr_map['# Item'] + '_' + str(index).zfill(4)

imfile = 'virt_' + label + '.tif'
	    
tiff.imsave(imfile,im4,compress=6)
    
cx = t_size[1]
cy = t_size[0]

a = [[0,0],[cx,0],[cx,cy],[0,cy],[0,0]]
a = numpy.matrix(a) - [cx/2 , cy/2]

a = a * px_scale
    
c1 = a * rotm1.T *rotmat + c

#c1 = a * rotmat1 * targetheader['pixelsize'] + c_stage
    
cnx = numpy.array(numpy.transpose(c1[:,1]))
cnx = numpy.array2string(cnx,separator=' ')
cnx = cnx[2:-2]
    
cny = numpy.array(numpy.transpose(c1[:,0]))
cny = " ".join(map(str,cny))
cny = cny[1:-2]
    
px = numpy.array(numpy.transpose(p4[:,1]))
px = numpy.array2string(px,separator=' ')
px = px[2:-2]

py = numpy.array(numpy.transpose(p4[:,0]))
py = numpy.array2string(py,separator=' ')
py = py[2:-2]
    
    
# fill navigator

# map for realignment
newnavitem = dict(targetitem)
newnavitem['MapFile'] = [imfile]
newnavitem.pop('StageXYZ','')
newnavitem.pop('RawStageXY','')
newnavitem['CoordsInAliMont'] = [str(c[0]),str(c[1]),curr_map['StageXYZ'][2]]
newnavitem['PtsY'] = cnx.split()
newnavitem['PtsX'] = cny.split()
newnavitem['Note'] = newnavitem['MapFile']
newnavitem['MapID'] = [str(mapid)]
newnavitem['DrawnID'] = curr_map['MapID']
newnavitem['Acquire'] = ['0']
newnavitem['MapSection'] = ['0']
newnavitem.pop('SamePosId','')
# newnavitem['MapWidthHeight'] = [str(im2size[0]),str(im2size[1])]
newnavitem['ImageType'] = ['2']
newnavitem['MapMinMaxScale'] = [str(numpy.min(im4)),str(numpy.max(im4))]
newnavitem['NumPts'] = ['5']
newnavitem['# Item'] = 'map_' + label    
    
curr_map['Acquire'] = ['0']

# Polygon
 
polynav=dict()
polynav['# Item'] = label
polynav['Color'] = ['1']
polynav['NumPts'] = [str(p.shape[0])]
polynav['Acquire'] = ['1']
polynav['Draw'] = ['1']
polynav['Regis'] = curr_map['Regis']
polynav['Type'] = ['1']
polynav['DrawnID'] = [str(mapid)]
polynav['GroupID'] = ['123456']#curr_map['MapID']
polynav['CoordsInMap'] = [str(int(cx/2)) , str(int(cy/2)),curr_map['StageXYZ'][2]]
polynav['PtsY'] = px.split()
polynav['PtsX'] = py.split()



outnav.append(curr_map)

outnav.append(newnavitem)

outnav.append(polynav)

for nitem in outnav:
 
  out = em.itemtonav(nitem,nitem['# Item'])
  for item in out: nnf.write("%s\n" % item)

            
nnf.close()

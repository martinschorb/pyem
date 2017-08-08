# -*- coding: utf-8 -*-

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


# PARAMETERS


navname = 'nav2.nav'
# file name navigator

maplabel = '9-A'
# label of the map in the navigator

points = range(945,1052)
# array of navlabels for all POIs

pxs_target = 39.8
# target pixel size of the extracted images (A)

imsz_target = [924,958]


# -------------------------------

# -------------------------------
# start script

# read and parse navigator file (version >2 !!)

if not os.path.exists(navname):
	print 'ERROR: ' + navname + ' does not exist! Exiting' + '\n'
	sys.exit(1)


nav_file = open(navname,"r")

navlines=list()

for line in nav_file.readlines():
    navlines.append(line.strip())

# we need an empty line at the end
navlines.append('')

# look for map item

searchstr = '[Item = ' + maplabel + ']'

mapitemstartline = navlines.index(searchstr)

mapitemendline = navlines[mapitemstartline:].index('')
  
mapitem = navlines[mapitemstartline:mapitemstartline+mapitemendline]




# extract map file name

mapfile = fnmatch.filter(mapitem, 'MapFile*')[0]

mapfile = mapfile[mapfile.find('= ')+2:]

if not os.path.exists(mapfile):
	print 'Warning: ' + mapfile + ' does not exist!' + '\n'
	
	mapfile = mapfile[mapfile.rfind('\\')+1:]
	print 'will try ' + mapfile + ' in current directory.' + '\n'

	
if not os.path.exists(mapfile):
	print 'ERROR: ' + mapfile + ' does not exist! Exiting' + '\n'
	sys.exit(1)
	

# get file information from map

callcmd = 'header ' + mapfile + ' > syscall.tmp'
os.system(callcmd)


headerfile = open('syscall.tmp',"r")

map_headerlines=list()

for line in headerfile.readlines():
    map_headerlines.append(line.strip())

head1 = fnmatch.filter(map_headerlines, 'Number of columns, *')[0]
strindex = head1.find('.. ')+3
oldindex = strindex
while strindex-oldindex < 2:
  oldindex = strindex
  strindex = head1.find(' ',strindex+1)
    
xsize = int(head1[oldindex+1:strindex])  

oldindex = strindex
while strindex-oldindex < 2:
  oldindex = strindex
  strindex = head1.find(' ',strindex+1)

ysize = int(head1[oldindex+1:strindex])
stacksize = int(head1[head1.rfind(' ')+1:])  


# check if map is a montage or not
mergefile = mapfile[:mapfile.rfind('.mrc')]
mergefile = mergefile + '_merged'

if stacksize < 2:
  callcmd = 'mrc2tif ' +  mapfile + ' ' + mergefile
    
else:
  # merge the montage to a single file
  
  
  callcmd = 'extractpieces ' +  mapfile + ' ' + mapfile + '.pcs'
  os.system(callcmd)
  
  print '----------------------------------------------------\n'
  print 'Merging the map montage into a single image....' + '\n'
  print '----------------------------------------------------\n'
  
  callcmd = 'blendmont -imi ' +  mapfile + ' -imo ' + mergefile + '.mrc -pli ' + mapfile + '.pcs -roo ' + mergefile  + '.mrc -sloppy' 
  #os.system(callcmd)
  
  callcmd = 'mrc2tif ' +  mergefile + '.mrc ' + mergefile +'.tif'
  
  
#os.system(callcmd)

ecdname = mergefile + '.mrc.ecd'
ecd_file = open(ecdname,"r")
ecdlines=list()
for line in ecd_file.readlines():
    print(line)
    ecdlines.append(line.strip())

    
    print(ecdlines)

    
break

    
mdocname = mapfile + '.mdoc'

# extract map corner coordinates

if stacksize > 1:
    #if available get info from mdoc file
    if os.path.exists(mdocname):
        mdoc_file = open(mdocname,"r")
        mdoclines=list()
        for line in mdoc_file.readlines():
            mdoclines.append(line.strip())
        
        tempmdoc = mdoclines
        
        montsearch = fnmatch.filter(mdoclines, '[MontSection *')[0]
        mdocstartline = mdoclines.index(montsearch)
        mont = mdoclines[mdocstartline:]
        

        montsize = fnmatch.filter(mont, 'PieceCoordinates *')[0]
        montsize = montsize[montsize.find('= ')+2:]
        mont_xsize = montsize[:montsize.find(' ')]
        mont_ysize = montsize[montsize.find(mont_xsize)+len(mont_xsize)+1:montsize.find(' 0')]
        
        mont_xsize = float(mont_xsize)
        mont_ysize = float(mont_ysize)
        
        montcenter = fnmatch.filter(mont, 'StagePosition *')[0]
        montcenter = montcenter[montcenter.find('= ')+2:]
        centerx = montcenter[:montcenter.find(' ')]
        centery = montcenter[montcenter.find(centerx)+len(centerx)+1:]
        
        centerx=float(centerx)
        centery=float(centery)

        tilecenter = numpy.zeros([2,stacksize])
        tileshifts = numpy.zeros([2,stacksize])
        
        
  
        for j in range(0, stacksize):
            tilestart = fnmatch.filter(tempmdoc, '[ZValue = *')[0]
            tilestartindex = tempmdoc.index(tilestart)
            tempmdoc = tempmdoc[tilestartindex+1:]
            
            tc = fnmatch.filter(tempmdoc, 'StagePosition = *')[0]
            tc = tc[16:]
            tilecenter[0,j] = float(tc[:tc.find(' ')])
            tilecenter[1,j] = float(tc[tc.find(' ')+1:])
            
            unshifted = fnmatch.filter(tempmdoc, 'PieceCoordinates = *')[0]
            unshifted = unshifted[19:]
            unshiftedx = int(unshifted[:unshifted.find(' ')])
            unshiftedy = int(unshifted[unshifted.find(' ')+1:-1])
            
            shifted = fnmatch.filter(tempmdoc, 'AlignedPieceCoords = *')[0]
            shifted = shifted[21:]
            shiftedx = int(shifted[:shifted.find(' ')])
            shiftedy = int(shifted[shifted.find(' ')+1:-1])
            
            tileshifts[0,j] = shiftedx - unshiftedx
            tileshifts[1,j] = shiftedy - unshiftedy

                        
        
    else:
        centerx = numpy.mean(mapx)
        centery = numpy.mean(mapy)
        
mapx = fnmatch.filter(mapitem, 'PtsX*')[0]
mapx = map(float,mapx[mapx.find('= ')+2:].split())
mapy = fnmatch.filter(mapitem, 'PtsY*')[0]
mapy = map(float,mapy[mapy.find('= ')+2:].split())                



# determine the scale

head2 = fnmatch.filter(map_headerlines, 'Pixel spacing *')[0]
strindex = head2.find('.. ')+3
oldindex = strindex
while strindex-oldindex < 2:
  oldindex = strindex
  strindex = head2.find(' ',strindex+1)
  
pixelsize = float(head2[oldindex+1:strindex]) / 10000 # in um


# determine rotation of coordinate frame

a12 = math.atan2((mapx[1]-mapx[2]),(mapy[1]-mapy[2]))
a43 = math.atan2((mapx[4]-mapx[3]),(mapy[4]-mapy[3]))
a23 = math.atan2((mapx[2]-mapx[3]),(mapy[2]-mapy[3]))
a14 = math.atan2((mapx[1]-mapx[4]),(mapy[1]-mapy[4]))


meanangle = numpy.mean([a12,a43,a23-math.pi/2,a14-math.pi/2])

# normalize coordinates

nmx = numpy.array(mapx) - centerx
nmy = numpy.array(mapy) - centery


# convert to Matrix notation

mat_mapcoos = numpy.array([[nmx],[nmy]])
mat_mapcoos = numpy.matrix(mat_mapcoos)

ct = math.cos(meanangle)
st = math.sin(meanangle)

rotmat = numpy.matrix([[ct,-st],[st,ct]])


# extract point coordinates
posx=list()
posy=list()
shiftid=list()

for i in points:
  # look for map item
  searchstr = '[Item = ' + str(i) + ']'  
  if searchstr not in navlines:
    print('item '+ str(i) + ' not found, skipping it...')
  else:
    itemstartline = navlines.index(searchstr)
    itemendline = navlines[itemstartline:].index('')
    ptitem = navlines[itemstartline:itemstartline+itemendline]
    xval=fnmatch.filter(ptitem, 'PtsX*')[0]
    xvalue = float(xval[xval.find('= ')+2:])
    
    yval=fnmatch.filter(ptitem, 'PtsY*')[0]
    yvalue = float(yval[yval.find('= ')+2:])
    
    
    # if mdoc available, correct for alignment shift
    if os.path.exists(mdocname):

        pt = numpy.array([[xvalue],[yvalue]])

        tiledist = sum((pt-tilecenter)**2)
        tileid = np.argmin(tiledist)
        shiftid.append(tileid)
        
  
    posx.append(xvalue)
    posy.append(yvalue)


    
# calculate the pixel coordinates for each point

npx = numpy.array(posx) - centerx
npy = numpy.array(posy) - centery

mat_ptcoos = numpy.array([[npx],[npy]])
mat_ptcoos = numpy.matrix(mat_ptcoos)


# rotate coordinate frame to match pixel axes

map_rot = rotmat * mat_mapcoos / pixelsize

min_x = numpy.min(map_rot[0,:])
min_y = numpy.min(map_rot[1,:])


map_rot[0,:] = map_rot[0,:] - min_x
map_rot[1,:] = map_rot[1,:] - min_y

pt_rot = rotmat * mat_ptcoos / pixelsize

pt_rot[0,:] = pt_rot[0,:] - min_x
pt_rot[1,:] = pt_rot[1,:] - min_y


# load merged map for cropping
from tifffile import imread

im = imread(mergefile + '.tif')

ix=0

for i in points:
    searchstr = '[Item = ' + str(i) + ']' 
    if searchstr in navlines:
        px_scale = pxs_target /( pixelsize * 10000 )

        imsz1 = numpy.array(imsz_target) * px_scale
        
        px = round(pt_rot[0,ix])
        py = round(pt_rot[1,ix])
                
        if os.path.exists(mdocname):
            px = px + tileshifts[0,shiftid[ix]]
            py = py + tileshifts[1,shiftid[ix]]
            
            #print(tileshifts[0,shiftid[ix]])
        
     #   print(imsz1)

        xel = range(int(px - imsz1[0]/2) , int(px + round(float(imsz1[0])/2)))
        yel = range(int(py - imsz1[1]/2) , int(py + round(float(imsz1[1])/2)))

        #print(xel)
        #print(yel)

        imsize = numpy.array(im.shape)

        im1=im[imsize[0] - yel,:]
        im1=im1[:,xel]

    #    print(points[i])
        im2 = scipy.misc.imresize(im1,1/px_scale)
    #    print(im2.shape)
    #    plt.imshow(im2)

        plt.imsave('virt_map_minus' + str(i) + '.png',np.uint8(im2),cmap=plt.get_cmap('gray'),origin='lower')


        ix=ix+1
#
#
#
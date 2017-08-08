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


navname = 'test.nav'
# file name navigator

maplabel = '9-A'
# label of the map in the navigator

points = range(1033,1052)
# array of navlabels for all POIs


target_map = 'refmap'


# -------------------------------
#cd /home/schorb/e/schorb/data/serialem_montages/wim_schmidt2
# -------------------------------

# define supporting functions



def loadtext(fname):

    # loads a text file, such as nav or adoc, returns it as a list
    
    if not os.path.exists(fname):
        print 'ERROR: ' + fname + ' does not exist! Exiting' + '\n'
        sys.exit(1)
    file = open(fname,"r")

    lines=list()

    for line in file.readlines():
        lines.append(line.strip())
    
    lines.append('')    
    return lines
    
# -------------------------------

def nav_item(navlines,label):
    
    # extracts the content block of a navItem of givel label
    # reads and parses navigator files version >2 !!

    searchstr = '[Item = ' + label + ']'
    if not searchstr in navlines:
        print('ERROR: Navigator Item ' + label + ' not found!')        
        result=[]        
    else:    
        itemstartline = navlines.index(searchstr)+1
        itemendline = navlines[itemstartline:].index('')

        item = navlines[itemstartline:itemstartline+itemendline]
        result = parse_adoc(item)
        
    return result
    
# -------------------------------

def mdoc_item(lines,label):
    
    # extracts the content block of an item of givel label in a mdoc file

    searchstr = '[' + label + ']'
    if not searchstr in lines:
        print('ERROR: Item ' + label + ' not found!')        
        result=[]
    else:    
        itemstartline = lines.index(searchstr)+1
        itemendline = lines[itemstartline:].index('')

        item = lines[itemstartline:itemstartline+itemendline]
        result = parse_adoc(item)
        
    return result


# -------------------------------

def parse_adoc(lines):
    # converts an adoc-format string into a dictionary
    answer = {}
    for line in lines:
        entry = line.split()
        if entry: answer.update({entry[0]: entry[2:]})

    
    return answer

# -------------------------------

def map_file(mapitem):
    
    # extracts map file name from navigator and checks for existance

    mapfile = mapitem['MapFile'][0]
    
    if not os.path.exists(mapfile):
        print 'Warning: ' + mapfile + ' does not exist!' + '\n'

        mapfile = mapfile[mapfile.rfind('\\')+1:]
        print 'will try ' + mapfile + ' in current directory.' + '\n'


    if not os.path.exists(mapfile):
        print 'ERROR: ' + mapfile + ' does not exist! Exiting' + '\n'
        sys.exit(1)

    return mapfile



# -------------------------------

def map_header(mapfile):
    
    # extracts MRC header information for a given file name
    header={}

    callcmd = 'header ' + mapfile + ' > syscall.tmp'
    os.system(callcmd)

    map_headerlines = loadtext('syscall.tmp')
    head1 = fnmatch.filter(map_headerlines, 'Number of columns, *')[0]
    strindex = head1.find('.. ')+3
    oldindex = strindex
    while strindex-oldindex < 2:
      oldindex = strindex
      strindex = head1.find(' ',strindex+1)

    header['xsize'] = int(head1[oldindex+1:strindex])

    oldindex = strindex
    while strindex-oldindex < 2:
      oldindex = strindex
      strindex = head1.find(' ',strindex+1)

    header['ysize'] = int(head1[oldindex+1:strindex])
    header['stacksize'] = int(head1[head1.rfind(' ')+1:])

    
    # determine the scale

    head2 = fnmatch.filter(map_headerlines, 'Pixel spacing *')[0]
    strindex = head2.find('.. ')+3
    oldindex = strindex
    while strindex-oldindex < 2:
        oldindex = strindex
        strindex = head2.find(' ',strindex+1)

    header['pixelsize'] = float(head2[oldindex+1:strindex]) / 10000 # in um

    return header

# -------------------------------
# -------------------------------
# -------------------------------
# -------------------------------


# start script


navlines = loadtext(navname)

mapitem = nav_item(navlines,maplabel)
targetitem = nav_item(navlines,target_map)

#extract target map properties

targetfile = map_file(targetitem)
targetheader = map_header(targetfile)


# extract map properties

mapfile = map_file(mapitem)
mapheader = map_header(mapfile)


# check if map is a montage or not
mergefile = mapfile[:mapfile.rfind('.mrc')]
mergefile = mergefile + '_merged'

if mapheader['stacksize'] < 2:
    callcmd = 'mrc2tif ' +  mapfile + ' ' + mergefile
    
else:
  # merge the montage to a single file


    callcmd = 'extractpieces ' +  mapfile + ' ' + mapfile + '.pcs'
    os.system(callcmd)

    print '----------------------------------------------------\n'
    print 'Merging the map montage into a single image....' + '\n'
    print '----------------------------------------------------\n'

    callcmd = 'blendmont -imi ' +  mapfile + ' -imo ' + mergefile + '.mrc -pli ' + mapfile + '.pcs -roo ' + mergefile  + '.mrc -al '+ mergefile + '.al -sloppy'    #os.system(callcmd)
#    os.system(callcmd)
    print(callcmd)
    callcmd = 'mrc2tif ' +  mergefile + '.mrc ' + mergefile +'.tif'
#    os.system(callcmd)
    

mdocname = mapfile + '.mdoc'

# extract map corner coordinates

if mapheader['stacksize'] > 1:
    #if available get info from mdoc file
    if os.path.exists(mdocname):
        mdoclines = loadtext(mdocname)
           
        mont = mdoc_item(mdoclines,'MontSection = 0')
        
        mont_xsize = float(mont['PieceCoordinates'][0])
        mont_ysize = float(mont['PieceCoordinates'][1])
               
        centerx = float(mont['StagePosition'][0])
        centery = float(mont['StagePosition'][1])
           
    else:
        centerx = numpy.mean(mapx)
        centery = numpy.mean(mapy)


        
        
        
        
# grab coordinates of map corner points        
        
mapx = map(float,mapitem['PtsX'])
mapy = map(float,mapitem['PtsY'])        

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
  # get coordinates from map item
    ptitem = nav_item(navlines,str(i))
    if ptitem:
        posx.append(float(ptitem['PtsX'][0]))
        posy.append(float(ptitem['PtsY'][0]))

# calculate the pixel coordinates for each point

npx = numpy.array(posx) - centerx
npy = numpy.array(posy) - centery

mat_ptcoos = numpy.array([[npx],[npy]])
mat_ptcoos = numpy.matrix(mat_ptcoos)


# rotate coordinate frame to match pixel axes

map_rot = rotmat * mat_mapcoos / mapheader['pixelsize']

min_x = numpy.min(map_rot[0,:])
min_y = numpy.min(map_rot[1,:])


map_rot[0,:] = map_rot[0,:] - min_x
map_rot[1,:] = map_rot[1,:] - min_y

pt_rot = rotmat * mat_ptcoos / mapheader['pixelsize']

pt_rot[0,:] = pt_rot[0,:] - min_x
pt_rot[1,:] = pt_rot[1,:] - min_y


# load merged map for cropping
from tifffile import imread

im = imread(mergefile + '.tif')

ix=0

for i in points:
    searchstr = '[Item = ' + str(i) + ']' 
    if searchstr in navlines:
        px_scale = targetheader['pixelsize'] /( mapheader['pixelsize'] * 10000 )

        imsz1 = numpy.array([targetheader['xsize'],targetheader['ysize']]) * px_scale
        
        px = round(pt_rot[0,ix])
        py = round(pt_rot[1,ix])
                
    #    if os.path.exists(mdocname):
     #       px = px + tileshifts[0,shiftid[ix]]
      #      py = py + tileshifts[1,shiftid[ix]]
            
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

    #    plt.imsave('virt_map_minus' + str(i) + '.png',np.uint8(im2),cmap=plt.get_cmap('gray'),origin='lower')


        ix=ix+1
#
#
#
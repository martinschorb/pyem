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
import re
from scipy.misc import imresize

# PARAMETERS


navname = 'test.nav'
# file name navigator

maplabel = '9-A'
# label of the map in the navigator

points = range(980,981)
# array of navlabels for all POIs


target_map = 'refmap'


# -------------------------------
# %cd /home/schorb/e/schorb/data/serialem_montages/wim_schmidt2
# -------------------------------

# define supporting functions



def loadtext(fname):

    # loads a text file, such as nav or adoc, returns it as a list
    
    if not os.path.exists(fname):
        print 'ERROR: ' + fname + ' does not exist! Exiting' + '\n'
        sys.exit(1)
    f = open(fname,"r")

    lines=list()

    for line in f.readlines():
        lines.append(line.strip())
    
    lines.append('')
    f.close()
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

def itemtonav(item,name):
    # converts a dictionary autodoc item variable into text list suitable for export into navigator format
    dlist = list()
    dlist.append('[Item = ' + name + ']')
    for key, value in item.iteritems():
        dlist.append(key + ' = ' + " ".join(value))
    
    dlist.append('')
    return dlist
    

    
    
# -------------------------------
# -------------------------------
# -------------------------------


# start script


navlines = loadtext(navname)

mapitem = nav_item(navlines,maplabel)
targetitem = nav_item(navlines,target_map)

newnav = navname[:-4] + '_automaps.nav'
nnf = open(newnav,'w')
for item in navlines: nnf.write("%s\n" % item)


#extract target map properties

targetfile = map_file(targetitem)
targetheader = map_header(targetfile)


# extract map properties

mapfile = map_file(mapitem)
mapheader = map_header(mapfile)

mappxcenter = [mapheader['xsize']/2, mapheader['ysize']/2]



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
#    print(callcmd)
    callcmd = 'mrc2tif ' +  mergefile + '.mrc ' + mergefile +'.tif'
    
#os.system(callcmd)


mergeheader = map_header(mergefile + '.mrc')


# load merged map for cropping
from tifffile import imread

im = imread(mergefile + '.tif')


# extract pixel coordinate of each tile

tilepx = loadtext(mergefile + '.al')
tilepx = tilepx[:-1]
for j, item in enumerate(tilepx): tilepx[j] = map(float,re.split(' +',tilepx[j]))
tilepx = scipy.delete(tilepx,2,1)


mdocname = mapfile + '.mdoc'


# extract center positions of individual map tiles
if mapheader['stacksize'] > 1:
    if os.path.exists(mdocname):
        mdoclines = loadtext(mdocname)
        tilepos=list()
        for i in range(0,mapheader['stacksize']):
            tilelines = mdoc_item(mdoclines,'ZValue = ' + str(i))
            tilepos.append(tilelines['StagePosition'])
        tilepos = numpy.array(tilepos,float)
            
    else:
        callcmd = 'extracttilts ' + mapfile + ' -stage -all > syscall.tmp'
        os.system(callcmd)
        tilepos1 = loadtext('syscall.tmp')[21:-1]
        tilepos=numpy.zeros([mapheader['stacksize']-1,2])
        for i, item in enumerate(tilepos1): tilepos[i] = map(float,tilepos1[i].split('  '))    
    
else:
    tilepos = map(float,mapitem['StageXYZ'][0:2])
    
    
# grab coordinates of map corner points        
        
mapx = map(float,mapitem['PtsX'])
mapy = map(float,mapitem['PtsY'])        

# determine rotation of coordinate frame

a12 = math.atan2((mapx[1]-mapx[2]),(mapy[1]-mapy[2]))
a43 = math.atan2((mapx[4]-mapx[3]),(mapy[4]-mapy[3]))
a23 = math.atan2((mapx[2]-mapx[3]),(mapy[2]-mapy[3]))
a14 = math.atan2((mapx[1]-mapx[4]),(mapy[1]-mapy[4]))


meanangle = numpy.mean([a12,a43,a23-math.pi/2,a14-math.pi/2])


# convert to Matrix notation

ct = math.cos(meanangle)
st = math.sin(meanangle)

rotmat = numpy.matrix([[ct,-st],[st,ct]])  



for i in points:
  # get coordinates from map item
    searchstr = '[Item = ' + str(i) + ']'  
    if searchstr not in navlines:
        print('item '+ str(i) + ' not found, skipping it...')
    else:
        
        ptitem = nav_item(navlines,str(i))
            
        if ptitem:
            xval = (float(ptitem['PtsX'][0]))
            yval = (float(ptitem['PtsY'][0]))
            
            pt = numpy.array([xval,yval])


            tiledist = numpy.sum((tilepos-pt)**2,axis=1)
            tileid = numpy.argmin(tiledist)
            
            # normalize coordinates
            
            ptn = numpy.matrix(pt - tilepos[tileid])

            # calculate the pixel coordinates
            
            pt_px = numpy.array(ptn * numpy.transpose(rotmat) / mapheader['pixelsize'] + mappxcenter)
            pt_px = pt_px.squeeze()
            pt_px1 = pt_px + tilepx[tileid]
            pt_px1[1] = mergeheader['ysize'] - pt_px1[1]
            
                      
            
            px_scale = targetheader['pixelsize'] /( mapheader['pixelsize'] )

            imsz1 = numpy.array([targetheader['xsize'],targetheader['ysize']]) * px_scale
        
            px = round(pt_px1[0])
            py = round(pt_px1[1])


            xel = range(int(px - imsz1[0]/2) , int(px + round(float(imsz1[0])/2)))
            yel = range(int(py - imsz1[1]/2) , int(py + round(float(imsz1[1])/2)))

            imsize = numpy.array(im.shape)
            
            im1=im[yel,:]

            im1=im1[:,xel]
#            %matplotlib inline
                      
     

        #    print(points[i])
            im2 = imresize(im1,1/px_scale)
            
            #print(im2.shape)
            #plt.imshow(im2)

            plt.imsave('virt_map_' + str(i) + '.png',numpy.uint8(im2),cmap=plt.get_cmap('gray'))
            
            
          # fill navigator  
            newnavitem = targetitem
            
            newnavitem['MapFile'] = 'virt_map_' + str(i) + '.png'
            newnavitem['StageXYZ'] = ptitem['StageXYZ']
            newnavitem['PtsX'] = ptitem['PtsX']
            newnavitem['PtsY'] = ptitem['PtsY']
            newnavitem['NumPts'] = '1'
            newnavitem['Note'] = newnavitem['MapFile']
            newnavitem['MapID'] = str(999900000 + i)
            newnavitem['Acquire'] = '1'
            
            outnav = itemtonav(newnavitem,str(i))
            
            for item in outnav: nnf.write("%s\n" % item)


            
nnf.close()

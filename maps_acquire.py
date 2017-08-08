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


navname = 'test.nav'
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
import IPython



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

    mapfile = ' '.join(mapitem['MapFile'])
    
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
      if not key == '# Item':	
        dlist.append(key + ' = ' + " ".join(value))
    
    dlist.append('')
    return dlist
    

    
    
# -------------------------------

def fullnav(navlines):
# parses a full nav file and returns a list of dictionaries
  c=[]
  for item in navlines:
    if item.find('[')>-1:
      b=nav_item(navlines,item[item.find(' = ') + 3:-1])
      b['# Item']=item[item.find(' = ') + 3:-1]
      c.append(b)
  
  return c



# -------------------------------



def mergemap(mapitem):

  m=dict()
 
  # extract map properties
 
    # grab coordinates of map corner points        
	  
  mapx = map(float,mapitem['PtsX'])
  mapy = map(float,mapitem['PtsY'])
    
  a=numpy.array([mapx,mapy])
  lx = numpy.sqrt(sum((a[:,2]-a[:,3])**2))
  ly = numpy.sqrt(sum((a[:,1]-a[:,2])**2))


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


  mapfile = map_file(mapitem)
  if mapfile.find('.st')<0 and mapfile.find('.map')<0 and mapfile.find('.mrc')<0:
    print 'Warning: ' + mapfile + ' is not an MRC file!' + '\n'
    print 'Assuming it is a single file or a stitched montage.' + '\n'
    mergefile = mapfile
    im = tiff.imread(mergefile)
    mappxcenter = numpy.array(im.shape)[0:2] / 2 
    mergeheader = {}
       
    mergeheader['stacksize'] = numpy.array(im.shape)
    mergeheader['xsize'] = numpy.array(im.shape)[0]
    mergeheader['ysize'] = numpy.array(im.shape)[1]
    mergeheader['pixelsize'] = numpy.mean([lx / numpy.array(im.shape)[0],ly / numpy.array(im.shape)[1]])
    mapheader = mergeheader

    
    
    tilepos = numpy.array([float(mapitem['PtsX'][0]),  float(mapitem['PtsY'][0])])
    
    
    
    tilepx = [0,0]
    tilepx=numpy.array([tilepx,tilepx])
    
  else:  
   
    
    mapheader = map_header(mapfile)

    mappxcenter = [mapheader['xsize']/2, mapheader['ysize']/2]



    # check if map is a montage or not
    mergefile = mapfile[:mapfile.rfind('.mrc')]     
    if mergefile == []: mergefile = mapfile
    
    mergefile = mergefile + '_merged'

    if mapheader['stacksize'] < 2:
	callcmd = 'mrc2tif ' +  mapfile + ' ' + mergefile
	tilepx = [0,0]
	tilepx=numpy.array([tilepx,tilepx])
	os.system(callcmd)

    else:
      if not os.path.exists(mergefile + '.mrc'):
	# merge the montage to a single file


	  callcmd = 'extractpieces ' +  mapfile + ' ' + mapfile + '.pcs'
	  os.system(callcmd)

	  print '----------------------------------------------------\n'
	  print 'Merging the map montage into a single image....' + '\n'
	  print '----------------------------------------------------\n'

	  callcmd = 'blendmont -imi ' +  mapfile + ' -imo ' + mergefile + '.mrc -pli ' + mapfile + '.pcs -roo ' + mergefile  + '.mrc -al '+ mergefile + '.al -sloppy'    #os.system(callcmd)
	  os.system(callcmd)
      #    print(callcmd)
	  
	 
	  callcmd = 'mrc2tif ' +  mergefile + '.mrc ' + mergefile +'.tif'
	  os.system(callcmd)
	  
	  
	  # extract pixel coordinate of each tile
      tilepx = loadtext(mergefile + '.al')
      tilepx = tilepx[:-1]
      for j, item in enumerate(tilepx): tilepx[j] = map(float,re.split(' +',tilepx[j]))
      tilepx = scipy.delete(tilepx,2,1)

	  
    


    mergeheader = map_header(mergefile + '.mrc')


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
	    tilepos = numpy.array([float(mapitem['PtsX'][0]),  float(mapitem['PtsY'][0])])    
	
    else:
	tilepos1 = map(float,mapitem['StageXYZ'][0:2])
	tilepos = numpy.array([tilepos1,tilepos1])
    
    mergefiletif = mergefile + '.tif'
      # load merged map for cropping

    im = tiff.imread(mergefiletif)
    
    
  # end MRC section
  



  # generate output

  m['mapfile'] = mapfile
  m['mergefile'] = mergefile
  m['rotmat'] = rotmat
  m['tilepos'] = tilepos
  m['im'] = im
  m['mappxcenter'] = mappxcenter
  m['mapheader'] = mapheader
  m['mergeheader'] = mergeheader
  m['tilepx'] = tilepx
  
  return m



# -------------------------------


  
  
def realign_map(item,allitems):
  if item['Type'] in [['0'],['1']]:
    # point or polygon    
    if not 'DrawnID' in item.keys():
      if not 'SamePosId' in item.keys():
	print('No map found to realign item '+ item['# Item'] + ' to, skipping it...')
	result=[]
      else: 
	result = realign_ID(nav_item(item['SamePosId']))
    else:
      mapID = item['DrawnID']

  else:
    #map
    if not 'RealignedID' in item.keys():
      print('No map found to realign item '+ item['# Item'] + ' to, skipping it...')
      result=[]
    else:
      mapID = item['RealignedID']
      
  result = filter(lambda item:item['MapID']==mapID,allitems)
  
  return result[0]

  




# -------------------------------


# -------------------------------



# -------------------------------




# -------------------------------





# start script


navlines = loadtext(navname)
targetitem = nav_item(navlines,target_map)

targetfile = map_file(targetitem)
targetheader = map_header(targetfile)


newnav = navname[:-4] + '_automaps.nav'
nnf = open(newnav,'w')
nnf.write("%s\n" % navlines[0])
nnf.write("%s\n" % navlines[1])


allitems = fullnav(navlines)



acq = filter(lambda item:item.get('Acquire'),allitems)
acq = filter(lambda item:item['Acquire']==['1'],acq)

non_acq = [x for x in allitems if x not in acq]

    
for item in non_acq:
  out = itemtonav(item,item['# Item'])
  for line in out: nnf.write("%s\n" % line)


maps = {}

newmapid = 1000

outnav=list()

for acq_item in acq:
  newmapid = newmapid + 1
  mapitem = realign_map(acq_item,allitems)
  
  itemid = mapitem['# Item']
  
  if not itemid in maps.keys():
    maps[itemid] = mergemap(mapitem)

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
    cny = cny[2:-2]
    
    
    
    
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
 
  out = itemtonav(nitem,nitem['# Item'])
  for item in out: nnf.write("%s\n" % item)

            
nnf.close()

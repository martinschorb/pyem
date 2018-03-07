# -*- coding: utf-8 -*-

# emtools.py

# Copyright (c) 2017, Martin Schorb
# Copyright (c) 2017, European Molecular Biology Laboratory
# Produced at the EMBL
# All rights reserved.

"""    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# dependencies
#%%
#import fnmatch
import os
import os.path
import sys
import numpy
import math
from scipy.ndimage.interpolation import zoom
from scipy.ndimage import rotate
import tifffile as tiff
import re
import mrcfile as mrc
import time

# define supporting functions


#%%

def loadtext(fname):

    # loads a text file, such as nav or adoc, returns it as a list

    if not os.path.exists(fname):
        print('ERROR: ' + fname + ' does not exist! Exiting' + '\n')
        sys.exit(1)
    f = open(fname,"r")

    lines=list()

    for line in f.readlines():
        lines.append(line.strip())

 #   lines.append('')
    f.close()
    return lines


# -------------------------------
#%%

def nav_item(lines,label):

    # extracts the content block of a navItem of givel label
    # returns it as a dictionary
    # reads and parses navigator adoc files version >2 !!
    if lines[-1] != '':
         navlines = lines+['']
    

    searchstr = '[Item = ' + label + ']'
    if not searchstr in navlines:
        print('ERROR: Navigator Item ' + label + ' not found!')
        result=[]
    else:
        itemstartline = navlines.index(searchstr)+1
        itemendline = navlines[itemstartline:].index('')

        item = navlines[itemstartline:itemstartline+itemendline]
        result = parse_adoc(item)
        result['# Item']=navlines[itemstartline-1][navlines[itemstartline-1].find(' = ') + 3:-1]

    return result


# -------------------------------
#%%

def mdoc_item(lines1,label):

    # extracts the content block of an item of givel label in a mdoc file
    # returns it as a dictionary
    if lines1[-1] != '':
        lines = lines1+['']


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
#%%

def parse_adoc(lines):
    # converts an adoc-format string list into a dictionary

    answer = {}
    for line in lines:
        entry = line.split()
        if entry: answer.update({entry[0]: entry[2:]})


    return answer

# -------------------------------
#%%

def map_file(mapitem):

    # extracts map file name from navigator and checks for existance
           
    mapfile = ' '.join(mapitem['MapFile'])
    cdir = os.getcwd()
    print(mapfile)

    if os.path.exists(mapfile):
        return mapfile
    
    else:
    #    print('Warning: ' + mapfile + ' does not exist!' + '\n')

       mapfile1 = mapfile[mapfile.rfind('\\')+1:]
       dir1 = mapfile[:mapfile.rfind('\\')]
       dir2=dir1[dir1.rfind('\\')+1:]

       print('will try ' + mapfile1 + ' in current directory or subdirectories.' + '\n')

       # check subdirectories recursively
        
       for subdir in os.walk(cdir):            
            mapfile = os.path.join(subdir[0],mapfile1)
           # print(' Try ' + mapfile)
            if os.path.exists(mapfile):                
                if subdir[2:] == dir2:
                    return mapfile
                else:
                    mapfile2 = mapfile
            else:
                print('ERROR: ' + mapfile1 + ' does not exist! Exiting' + '\n')
                # sys.exit(1)  # kills KNIME ;-)
                
            return mapfile2


# -------------------------------
#%%

def map_header(m):

    # extracts MRC header information for a given mrc.object (legacy from reading marc headers)
    header={}

    header['xsize'] = numpy.int(m.header.nx)
    header['ysize'] = numpy.int(m.header.ny)
    
    header['stacksize'] = numpy.int(m.header.nz)

    # determine the scale    

    header['pixelsize'] = m.voxel_size.x / 10000 # in um

    return header

# -------------------------------
#%%

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
#%%

def newmapID(allitems,mapid):
    # checks if provided item ID already exists in a navigator and gives the next unique ID
    # ID needs to be integer

    newid = mapid

    for item in allitems:
        if 'MapID' in item:
            if str(mapid) == item['MapID'][0]:
                newid = newmapID(mapid+1)

    return newid


# -------------------------------
#%%

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
#%%

def map_rotation(mapx,mapy):
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

  return rotmat


# -------------------------------
#%%

def mergemap(mapitem,crop=0):

  # processes a map item and merges the mosaic using IMOD
  # generates a dictionary with metadata for this procedure

  m=dict()
  m['Sloppy'] = False

  # extract map properties
  # grab coordinates of map corner points

  mapx = map(float,mapitem['PtsX'])
  mapy = map(float,mapitem['PtsY'])

  a=numpy.array([mapx,mapy])
  lx = numpy.sqrt(sum((a[:,2]-a[:,3])**2))
  ly = numpy.sqrt(sum((a[:,1]-a[:,2])**2))

  # determine map rotation
  rotmat = map_rotation(mapx,mapy)

  #find map file
  mapfile = map_file(mapitem)


  if mapfile.find('.st')<0 and mapfile.find('.map')<0 and mapfile.find('.mrc')<0:
    #not an mrc file

    print('Warning: ' + mapfile + ' is not an MRC file!' + '\n')
    print('Assuming it is a single tif file or a stitched montage.' + '\n')
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
   # map is mrc file
    mapsection = map(int,mapitem['MapSection'])[0]
    mf = mrc.mmap(mapfile, permissive = 'True')   
    
    mapheader = map_header(mf)
    pixelsize = mapheader['pixelsize']

    # determine if file contains multiple montages stored in one MRC stack

    mappxcenter = [mapheader['xsize']/2, mapheader['ysize']/2]

    mdocname = mapfile + '.mdoc'
    m['frames'] = map(int,mapitem['MapFramesXY'])


    if (m['frames'] == [0,0]):
      mapheader['stacksize'] = 0
      if os.path.exists(mdocname):
            mdoclines = loadtext(mdocname)
            pixelsize = float(mdoc_item(mdoclines,'ZValue = '+str(mapsection))['PixelSpacing'][0])/ 10000 # in um



    # extract center positions of individual map tiles
    if mapheader['stacksize'] > 1:

        montage_tiles = numpy.prod(m['frames'])
        if os.path.exists(mdocname):
            mdoclines = loadtext(mdocname)
            if mapheader['stacksize'] > montage_tiles:
            # multiple same-dimension montages in one MRC stack
                tileidx_offset = mapsection * montage_tiles
            elif mapheader['stacksize'] == montage_tiles:
            # single montage without empty tiles (polygon)
                tileidx_offset = 0
            elif  mapheader['stacksize'] < montage_tiles:
            # polygon fit montage with empty tiles
                tileidx_offset = 0

            tilepos=list()
            for i in range(0,numpy.min([montage_tiles,mapheader['stacksize']])-1):
                tile = mdoc_item(mdoclines,'ZValue = ' + str(tileidx_offset+i))                
                tilepos.append(tile['StagePosition'])
                if 'AlignedPieceCoordsVS' in tile: m['Sloppy'] = True

            tilepos = numpy.array(tilepos,float)
            pixelsize = float(mdoc_item(mdoclines,'MontSection = '+str(mapsection))['PixelSpacing'][0])/ 10000 # in um


        else:
            if mapheader['stacksize'] > montage_tiles:
                    raise Exception('Multiple maps stored in an MRC stack without mdoc file for metadata. I cannot reliably determine the pixel size.')


            callcmd = 'extracttilts ' + mapfile + ' -stage -all > syscall.tmp'
            os.system(callcmd)
            tilepos1 = loadtext('syscall.tmp')[21:-1]
            tilepos = numpy.array([float(mapitem['PtsX'][0]),  float(mapitem['PtsY'][0])])


    else:
        tilepos1 = map(float,mapitem['StageXYZ'][0:2])
        tilepos = numpy.array([tilepos1,tilepos1])


    # check if map is a montage or not
    mergefile = mapfile[:mapfile.rfind('.mrc')]
    if mergefile == []: mergefile = mapfile

    mergefile = mergefile + '_merged'

   # mergefiletif = mergefile  + '_s' + str(mapsection) + '.tif'
    mergeheader = mapheader

    if mapheader['stacksize'] < 2:
        print('Single image found. No merging needed.')
        #callcmd = 'mrc2tif -s -z ' + str(mapsection)+ ',' + str(mapsection) + ' ' +  mapfile + ' ' + mergefiletif
        tilepx = 0
        tilepx=numpy.array([tilepx,tilepx])
        #os.system(callcmd)
        merge_mrc =  mf
        mergeheader = mapheader
        overlapx = 0
        overlapy = 0
        tileloc = [0,0]

    else:
        if not os.path.exists(mergefile+'.mrc'):

            # merge the montage to a single file
            callcmd = 'extractpieces ' +  '\"' + mapfile + '\" \"'  +  mapfile + '.pcs\"'
            os.system(callcmd)

            print('----------------------------------------------------\n')
            print('Merging the map montage into a single image....' + '\n')
            print('----------------------------------------------------\n')

            callcmd = 'blendmont -imi ' + '\"' + mapfile + '\"' + ' -imo \"' + mergefile + '.mrc\" -pli \"' + mapfile + '.pcs\" -roo \"' + mergefile  + '.mrc\" -se ' + str(mapsection) + ' -al \"'+ mergefile + '.al\" -sloppy'    #os.system(callcmd)
            os.system(callcmd)
            #callcmd = 'mrc2tif ' +  mergefile + '.mrc ' + mergefiletif
            #os.system(callcmd)
            
        merge_mrc =  mrc.mmap(mergefile + '.mrc', permissive = 'True')
        mergeheader = map_header(merge_mrc)
        

            # extract pixel coordinate of each tile
        tilepx = loadtext(mergefile + '.al')

        tilepx = tilepx[:-1]
        for j, item in enumerate(tilepx): tilepx[j] = map(float,re.split(' +',tilepx[j]))

        tilepx = numpy.array(tilepx)
        tilepx = tilepx[tilepx[:,2] == mapsection,0:2]


        # use original tile coordinates(pixels) from SerialEM to determine tile position in montage

        tilepx1 = loadtext(mapfile + '.pcs')
        tilepx1 = tilepx1[:-1]
        for j, item in enumerate(tilepx1): tilepx1[j] = map(float,re.split(' +',tilepx1[j]))

        tilepx1 = numpy.array(tilepx1)
        tilepx1 = tilepx1[tilepx1[:,2] == mapsection,0:2]



        tpx = tilepx1[:,0]
        tpy = tilepx1[:,1]

        if numpy.abs(tpx).max()>0: xstep = tpx[tpx>0].min()
        else: xstep = 1
        if numpy.abs(tpy).max()>0: ystep = tpy[tpy>0].min()
        else: ystep = 1

        tileloc = numpy.array([tpx / xstep,tpy/ystep]).T

        m['sections'] = tileloc[:,0]*m['frames'][1]+tileloc[:,1]

        overlapx = mapheader['xsize'] - xstep
        overlapy = mapheader['ysize'] - ystep

        
	
	if crop>0:
		if not os.path.exists(mergefile+'_crop.mrc'):
			loopcount = 0
			print('waiting for crop model to be created ... Please store it under this file name: \"' + mergefile + '.mod\".')
			callcmd = '3dmod \"' +  mergefile + '.mrc\"'
			os.system(callcmd)
			while not os.path.exists(mergefile+'.mod'):
				if loopcount > 20: 
					print('Timeout - will continue without cropping!')
					break
				print('waiting for crop model to be created in IMOD... Please store it under this file name: \"' + mergefile + '.mod\".')
				time.sleep(20)
				loopcount = loopcount + 1
				
			if loopcount < 21:
				callcmd = 'imodmop \"' +  mergefile + '.mod\" \"'+ mergefile + '.mrc\" \"' + mergefile + '_crop.mrc\"'
				os.system(callcmd)
		
		merge_mrc.close()
		
		merge_mrc = mrc.mmap(mergefile + '_crop.mrc', permissive = 'True')
		
	
      # load merged map for cropping
    if mapsection>0:
        im = merge_mrc.data[mapsection,:,:]
    else:
        im = merge_mrc.data
        
    merge_mrc.close()    
    im = numpy.rot90(numpy.transpose(im))
    

  # end MRC section

  mergeheader['pixelsize'] = pixelsize
  mapheader['pixelsize'] = pixelsize


  # generate output

  m['mapfile'] = mapfile
  m['mergefile'] = mergefile+'.mrc'
  m['rotmat'] = rotmat
  m['tilepos'] = tilepos
  m['im'] = im
  m['mappxcenter'] = mappxcenter
  m['mapheader'] = mapheader
  m['mergeheader'] = mergeheader
  m['tilepx'] = tilepx
  m['overlap'] = [overlapx,overlapy]
  m['tileloc'] = tileloc
  
  merge_mrc.close()
  return m



# -------------------------------
#%%

def realign_map(item,allitems):
  # determines which map to align to for given navigator item

  if item['Type'] in [['0'],['1']]:
    # point or polygon
    if not 'DrawnID' in item.keys():
      if not 'SamePosId' in item.keys():
          print('No map found to realign item '+ item['# Item'] + ' to, skipping it...')
          result=[]
      else:
          result = realign_map(nav_item(item['SamePosId']),allitems)
    else:
      mapID = item['DrawnID']

  else:

    if not 'RealignedID' in item.keys():
      print('No map found to realign item '+ item['# Item'] + ' to, skipping it...')
      result=[]
    else:
      mapID = item['RealignedID']

  result = filter(lambda item:item['MapID']==mapID,allitems)

  return result[0]

# -------------------------------------

def imcrop(im1,c,sz):
  # crops an image of a given size (2 element numpy array) around a pixel coordinate (2 element numpy array)
  # in case the coordinate is close to an edge, the cropped image will have the maximum possible width/height
  # and centering of the image

  sz_x = sz[0]
  sz_y = sz[1]

  ximsz = im1.shape[0]
  yimsz = im1.shape[1]

  xllim = max([0,c[1]-sz_x/2])
  xulim = min([ximsz,c[1]+sz_x/2])

  x_range = min([c[1]-xllim,xulim-c[1]])
  xel = range(int(c[1] - x_range), int(c[1] + x_range))

  yllim = max([0,c[0]-sz_y/2])
  yulim = min([yimsz,c[0]+sz_y/2])

  y_range = min([c[0]-yllim,yulim-c[0]])

  yel = range(int(c[0] - y_range), int(c[0] + y_range))

  im2 = im1[xel,:]
  im2 = im2[:,yel]

  return im2


# --------------------------------------
#%%

def cart2pol(c):
    # cartesian into polar coordinates (2D)
            rho = numpy.sqrt(c[:,0]**2 + c[:,1]**2)
            phi = numpy.arctan2(c[:,1], c[:,0])
            return(numpy.transpose([phi,rho]))

# --------------------------------------

def pol2cart(rho, phi):
    # polar into cartesian coordinates (2D)
             x = rho * numpy.cos(phi)
             y = rho * numpy.sin(phi)
             return(numpy.transpose([x, y]))


# --------------------------------------
#%%

def img2polygon(img, n_poly, center, radius):
    #

  if img.dtype.kind is 'b':
    thresh = 1
  elif img.dtype.kind is 'i':
    thresh = 2**(8*img.dtype.itemsize-1)-1
    if img.max()<thresh:
        thresh = img.max()/2
  else: thresh = img.max()/2

  n_poly = n_poly + 1

  xs , ys = img.shape

  polypt = numpy.empty((0,2))

  polyphi = numpy.linspace(0,2*numpy.pi,n_poly)

  endpts = pol2cart(radius,polyphi)

  endpts = numpy.array(center) + endpts

  for pt in endpts:
    x, y = numpy.linspace(center[0], pt[0] , radius), numpy.linspace(center[1], pt[1], radius)
    a, b = x.astype(numpy.int),y.astype(numpy.int)
    a[a>(ys-1)] = ys-1
    a[a<0] = 0
    b[b>(xs-1)] = xs-1
    b[b<0] = 0
    lpx = img[b,a]
    lpd = numpy.diff(lpx)
    maxdiff = numpy.max(numpy.abs(lpd))
    maxdiff_ix = numpy.argmax(numpy.abs(lpd))
    if maxdiff < thresh:
      maxdiff_ix = radius-1

    polypt = numpy.append(polypt,[(a[maxdiff_ix],b[maxdiff_ix])],axis=0)

  return polypt

# --------------------------------------

def map_extract(im,c,p,px_scale,imsz1,rotm1):

  # extract image (1.42x to enable rotation)
  cropsize = imsz1 * 1.42

  angle = math.degrees(math.acos(rotm1[0,0]))

  im1 = imcrop(im,c,cropsize)

  # center to origin
  p1 = p - c

  # interpolate image
  im2 = zoom(im1,1/px_scale)

  p2 = p1/px_scale

  # rotate
  im3 = rotate(im2,angle,cval=numpy.mean(im1))
  p3 =  p2 * rotm1.T

  t_size = imsz1/px_scale
  c3 = numpy.array(im3.shape)/2

  #crop to desired size

  im4 = imcrop(im3,[c3[1],c3[0]],t_size)

  p4=p3.copy()

  p4[:,0] =  t_size[0]/2 - p3[:,0]
  p4[:,1] =  p3[:,1] + t_size[1]/2

  return im4, p4




# --------------------------------------


def pts2nav(im,pts,cntrs,curr_map,targetitem,nav,sloppy=False):
# takes pixel coordinates on an input map, generates virtual maps at their positions, creates polygons matching their shape.
# input parameters:
# - im, original image for feature detection
# - pts, image coordinates, list of arrays (for polygons)
# - cntrs, center of the feature (bounding box)
# - curr_map, map item to process (emtools dict)
# - targetitem, target map
# - nav, all navigator items (emtools dict)
# - sloppy (optional) if merging of original map was sloppy



  #parse input data

  if type(im) != numpy.ndarray:
      raise Exception('Wrong input format of image.')

  if type(pts) != list:
      if type(pts) == numpy.ndarray: pts = [pts]
      else: raise Exception('Wrong input format of point coordinates.')

  if type(cntrs) != list:
      if type(cntrs) == numpy.ndarray: cntrs = [cntrs]
      else: raise Exception('Wrong input format of center coordinates.')
  else:
      if len(cntrs) == 2:
          if type(cntrs[0]) == int:  cntrs = [cntrs]
          elif (type(cntrs[0]) != numpy.ndarray) and (type(cntrs[0]) != list):
              raise Exception('Wrong input format of center coordinates.')

# generate output
  outnav=list()
  nav_pol=list()
  nav_maps=list()


  # read information from maps

  mapfile = map_file(curr_map)
  map_mrc = mrc.mmap(mapfile, permissive = 'True')
  mapheader = map_header(map_mrc)

  pixelsize = mapheader['pixelsize']

  mx = map(float,curr_map['PtsX'])
  my = map(float,curr_map['PtsY'])

  rotmat = map_rotation(mx,my)
  imsz = numpy.array(im.shape)


  # target reference

  targetfile = map_file(targetitem)
  target_mrc = mrc.mmap(targetfile, permissive = 'True')
  targetheader = map_header(target_mrc)

  tx = map(float,targetitem['PtsX'])
  ty = map(float,targetitem['PtsY'])

  targetrot = map_rotation(tx,ty)

  # combine rotation matrices
  rotm1 = rotmat.T * targetrot

  px_scale = targetheader['pixelsize'] /pixelsize

  imsz1 = numpy.array([targetheader['xsize'],targetheader['ysize']]) * px_scale

  ntotal = len(cntrs)

  outnav.append(curr_map)

  curr_id = int(curr_map['MapID'][0])

  delim = 100000

  startid = newmapID(nav,divmod(curr_id,delim)[0]*delim)



  mapid = startid + 1
  idx=0

  for c in cntrs:

    polynav=dict()
    newnavitem = dict(targetitem)
    mapid = newmapID(nav,mapid+1)

    print('Processing object '+ str(idx+1) + '/' + str(ntotal) + ' (%2.0f%%)' %(idx*100/ntotal) + ' at position %5u , %5u' %(c[0],c[1]))

    p = pts[idx]

    im4, p4 = map_extract(im,c,p,px_scale,imsz1,rotm1)


    if min(im4.shape) < 400:
      print('Item is too close to border of map, skipping it.')
      ntotal = ntotal - 1
      continue

    

    px = numpy.array(numpy.transpose(p4[:,0]))
    px = numpy.array2string(px,separator=' ')
    px = px[2:-2]

    py = numpy.array(numpy.transpose(p4[:,1]))
    py = numpy.array2string(py,separator=' ')
    py = py[2:-2]


    if numpy.shape(p4)[0] == 1:
        polynav['Type'] = ['0']
        polynav['Color'] = ['0']
        polynav['NumPts'] = ['1']

    else:
        polynav['Type'] = ['1']
        polynav['Color'] = ['1']
        polynav['NumPts'] = [str(p.shape[0])]



    label = curr_map['# Item'] + '_' + str(idx).zfill(3)
    idx = idx + 1
    imfile = 'virt_' + label + '.tif'

    if os.path.exists(imfile): os.remove(imfile)
    tiff.imsave(imfile,im4,compress=6)

    t_size = imsz1/px_scale

    cx = t_size[1]
    cy = t_size[0]

    a = [[0,0],[cx,0],[cx,cy],[0,cy],[0,0]]
    a = numpy.matrix(a) - [cx/2 , cy/2]

    a = a * px_scale

    c_out = c

    c_out[1] = imsz[0] -c_out[1]

    c1 = a + c

    #c1 = a * rotmat1 * targetheader['pixelsize'] + c_stage

    cnx = numpy.array(numpy.transpose(c1[:,0]))
    cnx = numpy.array2string(cnx,separator=' ')
    cnx = cnx[2:-2]

    cny = numpy.array(numpy.transpose(c1[:,1]))
    cny = " ".join(map(str,cny))
    cny = cny[1:-2]





    # fill navigator

    # map for realignment

    newnavitem['MapFile'] = [imfile]
    newnavitem.pop('StageXYZ','')
    newnavitem.pop('RawStageXY','')
    if curr_map['MapFramesXY'] == ['0', '0']:
        newnavitem['CoordsInMap'] = [str(c_out[0]),str(c_out[1]),curr_map['StageXYZ'][2]]
    elif sloppy:
        newnavitem['CoordsInAliMontVS'] = [str(c_out[0]),str(c_out[1]),curr_map['StageXYZ'][2]]
    else:
        newnavitem['CoordsInAliMont'] = [str(c_out[0]),str(c_out[1]),curr_map['StageXYZ'][2]]

    newnavitem['PtsX'] = cnx.split()
    newnavitem['PtsY'] = cny.split()
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
    newnavitem['# Item'] = 'm_' + label
    newnavitem['GroupID'] = [str(newmapID(nav,startid+50000))]
    curr_map['Acquire'] = ['0']

    # Polygon

    polynav['# Item'] = label
    polynav['Acquire'] = ['1']
    polynav['Draw'] = ['1']
    polynav['Regis'] = curr_map['Regis']
    polynav['DrawnID'] = [str(mapid)]
    polynav['CoordsInMap'] = [str(int(cx/2)) , str(int(cy/2)),curr_map['StageXYZ'][2]]
    polynav['PtsX'] = px.split()
    polynav['PtsY'] = py.split()
    polynav['GroupID'] = [str(newmapID(nav,startid+70000))]

    nav_maps.append(newnavitem)

    nav_pol.append(polynav)



  outnav.extend(nav_maps)
  outnav.extend(nav_pol)



  return outnav

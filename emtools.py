# -*- coding: utf-8 -*-

# dependencies
#%%
import fnmatch
import os
import os.path
import sys
import numpy
import scipy
import math
from scipy.ndimage.interpolation import zoom
from scipy.ndimage import rotate
import tifffile as tiff
import re
import scipy.misc as spm

#%%
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
        result['# Item']=navlines[itemstartline-1][navlines[itemstartline-1].find(' = ') + 3:-1]
        
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
#%%
    
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
#%%
    
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

def mergemap(mapitem):
#%%
  m=dict()
 
  # extract map properties
 
    # grab coordinates of map corner points        
	  
  mapx = map(float,mapitem['PtsX'])
  mapy = map(float,mapitem['PtsY'])
    
  a=numpy.array([mapx,mapy])
  lx = numpy.sqrt(sum((a[:,2]-a[:,3])**2))
  ly = numpy.sqrt(sum((a[:,1]-a[:,2])**2))

  rotmat = map_rotation(mapx,mapy)


  mapfile = map_file(mapitem)
  #%%
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
    mergeheader = mapheader
    
    if mapheader['stacksize'] < 2:
	print 'Single image found. No merging needed.'
	
	callcmd = 'mrc2tif ' +  mapfile + ' ' + mergefile + '.tif'
	tilepx = [0,0]
	tilepx=numpy.array([tilepx,tilepx])
	os.system(callcmd)
	mergeheader = mapheader
	
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
	  mergeheader = map_header(mergefile + '.mrc')
	  
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

# -------------------------------------

def imcrop(im1,c,sz):

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



def cart2pol(c):
            rho = numpy.sqrt(c[:,0]**2 + c[:,1]**2)
            phi = numpy.arctan2(c[:,1], c[:,0])
            return(numpy.transpose([phi,rho]))
            
# --------------------------------------            
            
def pol2cart(rho, phi):
             x = rho * numpy.cos(phi)
             y = rho * numpy.sin(phi)
             return(numpy.transpose([x, y]))


# --------------------------------------

def img2polygon(img, n_poly, center, radius):
  if img.dtype.kind is 'b':
    thresh = 1
  elif img.dtype.kind is 'i':
    thresh = 2**(8*img.dtype.itemsize-1)-1
    if img.max()<thresh:
        thresh = img.max()/2
  else: thresh = img.max()/2
  
  n_poly = n_poly + 1

  xs , ys = img.shape
   
  polypt=numpy.empty((0,2))

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


def pts2nav(im,pts,cntrs,curr_map,targetitem,nav): 

  #parse input data
  
  if type(im) <> numpy.ndarray:
    raise Exception('Wrong input format of image.')

  if type(pts) <> list:
    if type(pts) == numpy.ndarray: pts = [pts]
    else: raise Exception('Wrong input format of point coordinates.')
  
  if type(cntrs) <>list:
    if type(cntrs) == numpy.ndarray: cntrs = [cntrs]
    else: raise Exception('Wrong input format of center coordinates.')
  else: 
    if len(cntrs) == 2:
      if type(cntrs[0]) == int:  cntrs = [cntrs]
      elif (type(cntrs[0]) <> numpy.ndarray) and (type(cntrs[0]) <> list):    
	raise Exception('Wrong input format of center coordinates.')
  

  # generate output
  outnav=list()
  nav_pol=list()
  nav_maps=list()


  # read information from maps
    
  mapfile = map_file(curr_map)
  mapheader = map_header(mapfile)

  pixelsize = mapheader['pixelsize']

  mx = map(float,curr_map['PtsX'])
  my = map(float,curr_map['PtsY'])

  rotmat = map_rotation(mx,my)
  imsz = numpy.array(im.shape)
  
  
  # target reference
  
  targetfile = map_file(targetitem)
  targetheader = map_header(targetfile)

  tx = map(float,targetitem['PtsX'])
  ty = map(float,targetitem['PtsY'])
    
  targetrot = map_rotation(tx,ty)
  
  # combine rotation matrices
  rotm1 = rotmat.T * targetrot
  angle = math.degrees(math.acos(rotm1[0,0]))

  px_scale = targetheader['pixelsize'] /pixelsize  

  imsz1 = numpy.array([targetheader['xsize'],targetheader['ysize']]) * px_scale
  
  ntotal = len(cntrs)
  
  outnav.append(curr_map)
  
  curr_id = int(curr_map['MapID'][0])
  
  delim = 100000
    
  startid = newmapID(nav,divmod(curr_id,delim)[0]*delim)
   
  
  mapid = startid + 1
  
  for idx,c in enumerate(cntrs):
    
    polynav=dict()
    newnavitem = dict(targetitem)
    mapid = newmapID(nav,mapid+1)
  
    
    print('Processing object '+ str(idx+1) + '/' + str(ntotal) + ' (%2.0f%%)' %(idx*100/ntotal) + ' at position %5u , %5u' %(c[0],c[1]))
    
    px = round(c[0])
    py = round(c[1])


    # extract image (1.42x to enable rotation)
    cropsize = imsz1 * 1.42
    

    im1 = imcrop(im,c,cropsize)

    if min(im1.shape) < 400:    
      print('Item is too close to border of map, skipping it.')
      continue
    
    p = pts[idx]
    
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
	
    px = numpy.array(numpy.transpose(p4[:,0]))
    px = numpy.array2string(px,separator=' ')
    px = px[2:-2]

    py = numpy.array(numpy.transpose(p4[:,1]))
    py = numpy.array2string(py,separator=' ')
    py = py[2:-2]
      
      
    if numpy.shape(p3)[0] == 1:
      polynav['Type'] = ['0']
      polynav['Color'] = ['0']
      polynav['NumPts'] = ['1']
      
    else:      
      polynav['Type'] = ['1']
      polynav['Color'] = ['1']
      polynav['NumPts'] = [str(p.shape[0])]

      
      
    label = curr_map['# Item'] + '_' + str(idx+1).zfill(3)
    
    imfile = 'virt_' + label + '.tif'
		
    if not os.path.exists(imfile):tiff.imsave(imfile,im4,compress=6)
	
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



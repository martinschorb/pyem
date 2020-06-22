# -*- coding: utf-8 -*-

# pyEM.py

# Copyright (c) 2020, Martin Schorb
# Copyright (c) 2020, European Molecular Biology Laboratory
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

# Python module for interpreting and modifying Navigator files created using SerialEM. For detailed information,
# see  https://doi.org/10.1038/s41592-019-0396-9
# Information and documentation of the individual functions can be found in Readme.md

# dependencies
#%%
#import fnmatch
import os
import os.path
import sys
import numpy
import skimage.transform as tf
import copy
from skimage import io
import re
import mrcfile as mrc
import time
from operator import itemgetter
import fnmatch
from subprocess import Popen, PIPE
import xml.etree.ElementTree as ET

# get python version
py_ver = sys.version_info

# get IMOD version
p1 = Popen("imodinfo", shell=True, stdout=PIPE)
o=list()
for line in p1.stdout:
    o.append(line)
o1=str(o[0]).split(' ')
imod_ver = list(map(int,o1[o1.index('Version')+1].split('.')))

# define functions


#%%

def loadtext(fname):

    # loads a text file, such as nav or adoc, returns it as a list of strings

    # check if file exists
    if not os.path.exists(fname):
        print('ERROR: ' + fname + ' does not exist! Exiting' + '\n')
        sys.exit(1)
    f = open(fname,"r")

    lines=list()

    for line in f.readlines():
        lines.append(line.strip())

    f.close()
    return lines


# -------------------------------
#%%

def nav_item(inlines,label):

    # extracts the content block of a single navItem of givel label
    # reads and parses navigator adoc files version >2, also in XML format !!
    # returns the first item found as a dictionary and the remaining list with that item removed
    # this is useful when multiple items have the exact same label and the function is called from within a loop to retrieve them all.

    
    lines=inlines[:]
    
    if(lines[0]=='<?xml version="1.0" encoding="utf-8"?>'):
      #load XML
      root = ET.fromstringlist(lines)
      el = root.findall('*[@name="%s"]' %label)
      root.remove(el[0])
      newroot = ET.Element('navigator')
      newroot.append(el[0])
      
      result = xmltonav(ET.tostringlist(newroot))[0]
      lines = ET.tostringlist(root)
      
    else:    
        if lines[-1] != '':
             lines = lines+['']
        
        # search for a navigator item of given label
        searchstr = '[Item = ' + label + ']'
        if not searchstr in lines:
            print('ERROR: Navigator Item ' + label + ' not found!')
            result=[]
        else:
            itemstartline = lines.index(searchstr)+1
            itemendline = lines[itemstartline:].index('')
    
            item = lines[itemstartline:itemstartline+itemendline]
            result = parse_adoc(item)
            # create a dictionary entry that contains the label. Comment # is given in case it is exported directly.
            result['# Item']=lines[itemstartline-1][lines[itemstartline-1].find(' = ') + 3:-1]
            
            lines[itemstartline-1:itemstartline+itemendline+1]=[]
            
    return result,lines
    


# -------------------------------
#%%

def mdoc_item(lines1,label,header=False):

    # extracts the content block of an item of given label in a mdoc file
    # returns it as a dictionary
    if lines1[-1] != '':
        lines = lines1+['']
        
    if header:
        item = lines[:lines.index('')]
    else:
        # search for mdoc key item with the given label
        searchstr = '[' + label + ']'
        if not searchstr in lines:
            print('ERROR: Item ' + label + ' not found!')
            item=[]
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

    output = {}
    for line in lines:
        entry = line.split()
        if entry: output.update({entry[0]: entry[2:]})

    return output

# -------------------------------
#%%

def map_file(mapitem):

    # extracts map file name from navigator and checks for existance
    

    # get string from navigator item       
    mapfile = ' '.join(mapitem['MapFile'])
    cdir = os.getcwd()

    if os.path.exists(mapfile):
        return mapfile
        print('current map: ' + mapfile)
    else:
    #    print('Warning: ' + mapfile + ' does not exist!' + '\n')
       mapfile1 = mapfile[mapfile.rfind('\\')+1:]
       dir1 = mapfile[:mapfile.rfind('\\')]
       dir2=dir1[dir1.rfind('\\')+1:]

     #  print('will try ' + mapfile1 + ' in current directory or subdirectories.' + '\n')

       # check subdirectories recursively
        
       for subdir in list(os.walk(cdir)):                 
            mapfile = os.path.join(subdir[0],mapfile1)
           # print(' Try ' + mapfile)
            if os.path.exists(mapfile):                
                mapfound=True
                if (subdir[0] == cdir or subdir[0] == os.path.join(cdir,dir2)):
                    return mapfile                
                else:
                    mapfile2 = mapfile
                    
            else:
                mapfound=False
        
       if not mapfound:
            print('ERROR: ' + mapfile1 + ' does not exist! Exiting' + '\n')
            sys.exit(1)  # kills KNIME ;-)
            
       return mapfile2


# -------------------------------
#%%
def findfile(searchstr, searchdir):
    
    # will find files that match a search string in subfolders of the provided search directory
    output = list()
    for rootdir,dirs,files in os.walk(searchdir):
        for file in files:
            if fnmatch.fnmatch(file,searchstr):
                output.append(os.path.join(rootdir,file))
    return output


# -------------------------------
#%%
def map_header(m):

    # extracts MRC header information for a given mrc.object (legacy from reading mrc headers)
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
    
    # Python 2 
    if py_ver[0] <3 :
      for key, value in item.iteritems():
        if not key == '# Item':
          dlist.append(key + ' = ' + " ".join(value))
    else:    
    # Python 3+    
      for key, value in item.items():
        if not key == '# Item':
          dlist.append(key + ' = ' + " ".join(value))
    dlist.append('')
    return dlist

# -------------------------------

#%%

def write_navfile(filename,outitems,xml=False):
    # creates a new navigator file from a list of navItems (default is mdoc format)
    allitems = copy.deepcopy(outitems)
    
    if xml:
        root = ET.Element('navigator')
        pd = ET.SubElement(root, 'PreData')
        adv = ET.SubElement(pd, 'AdocVersion')
        adv.text = '2.00'
        lsa = ET.SubElement(pd, 'LastSavedAs')
        lsa.text = filename
        
        for item in allitems:
            ci = ET.SubElement(root, 'Item')
            ci.set('name',item['# Item'])
            
            for key,val in item.items():
                if not key == '# Item':
                    cp = ET.SubElement(ci,key)
                    cp.text = ' '.join(val)
        indent_xml(root)
        tree = ET.ElementTree(root)        
        tree.write(filename,encoding="utf-8",xml_declaration=True)

        
    else:
        # MDOC format
        head0 = 'AdocVersion = 2.00'
        head1 = 'LastSavedAs = '+filename
    
        nnf = open(filename,'w')
        nnf.write("%s\n" % head0)
        nnf.write("%s\n" % head1)
        nnf.write("\n")
        
        # fill the new file   
        for nitem in allitems: 
            out = itemtonav(nitem,nitem['# Item'])
            for item in out: nnf.write("%s\n" % item)
                
        nnf.close()
        

# -------------------------------
        
# pretty print xml, from:
# http://effbot.org/zone/element-lib.htm#prettyprint
        
def indent_xml(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent_xml(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
        

# ------------------------------
        
        
#%%

def newID(allitems,startid):
    # checks if provided item ID already exists in a navigator and gives the next unique ID
    # ID needs to be integer

    newid = startid

    for item in allitems:
        if 'MapID' in item:
            if str(startid) == item['MapID'][0]:
                newid = newID(allitems,startid+1)

    return newid


# -------------------------------
#%%

def newreg(navitems):
    # gives the next available registration for the input set of navigator items 

    reg = list()
    for item in navitems : reg.append(int(item['Regis'][0]))

    return max(reg)+1


# -------------------------------    

#%%

def fullnav(inlines,header=False):
# parses a full nav file and returns a list of dictionaries
    
  navlines=inlines[:]
  
  if(navlines[0]=='<?xml version="1.0" encoding="utf-8"?>'):
      #load XML
      c = xmltonav(navlines)
  else:
      # mdoc format
      c=[]
      for index,item in enumerate(navlines):
        if item.find('[')>-1:
            if header:
                return inlines[:index-1]            
                
            (b,navlines)=nav_item(navlines,item[item.find(' = ') + 3:-1])
            b['# Item']=item[item.find(' = ') + 3:-1]
            c.append(b)

  return c

# -------------------------------
#%%
  
def xmltonav(navlines):
        
  root = ET.fromstringlist(navlines)
    
  c=[];
    
  for child in root:
      if child.tag == 'Item':
          item = dict({'# Item':child.attrib['name']})
          for prop in child:
              item[prop.tag] = prop.text.split(' ')
          c.append(item)    
          
  return c  



# -------------------------------
#%%

def navlabel_match(navitems,searchstr):
# identifies navigator items whose labels contain the given string

    r=re.compile(r'.*'+searchstr+'.*')
    
    return list(filter(lambda item:r.match(item['# Item']),navitems))


# -------------------------------
#%%

def duplicate_items(navitems,labels=[],prefix='',reg=True,maps=False):
# duplicates items from a list, optional second parameter is a list of labels of the items to duplicate.
# Default is to use the 'Acquire' flag. Third parameter defines a prefix for the created duplictes (defatul:none)
# The fourth parameter determines whether the registration of duplicate items should be changed (default:yes)
# if the maps flag is set, all maps that contain the label of the selected items or that were used to draw these are duplicated as well.

    
  outitems = copy.deepcopy(navitems)
  
  if labels==[]:
      dupitems = nav_selection(navitems)
      for item in dupitems : item['Acquire'] = ['0']
      
      
  else:
      dupitems = nav_selection(navitems,labels,False) 
      
      
  if reg:
      new_reg = [str(newreg(dupitems))]
  else:
      new_reg = dupitems[0]['Regis']
    

  for item in dupitems :
      newitem = copy.deepcopy(item)
            
      newitem['Regis'] = new_reg
      newitem['# Item'] = prefix + item['# Item']
      newitem['MapID'] = [str(newID(outitems,int(newitem['MapID'][0])))]
      
      if maps:
          drawnmap = realign_map(newitem,navitems)
          
          if (not drawnmap == []):    
              dupdrawn = copy.deepcopy(drawnmap)
              dupdrawn['# Item'] = prefix + drawnmap['# Item']
              dupdrawn['MapID'] = [str(newID(outitems,int(dupdrawn['MapID'][0])))]
              newitem['DrawnID'] = dupdrawn['MapID']                     
              
              othermaps = navlabel_match(navitems,dupdrawn['# Item'])
              othermaps.pop(othermaps.index(nav_selection(othermaps,sel=dupdrawn['# Item'],acquire=False)[0])); 
              
              dupdrawn['Regis'] = new_reg                                           
                                                           
              outitems.append(dupdrawn)                               
                                                           
              
              
      outitems.append(newitem)
    
  return outitems    
    

# -------------------------------------


def map_matrix(mapitem):
  # calculates the matrix relating pixel and stage coordinates  
    
  return numpy.matrix(list(map(float,mapitem['MapScaleMat']))).reshape(2,2)*(int(mapitem['MapBinning'][0])/int(mapitem['MontBinning'][0]))


# -------------------------------
#%%

def mergemap(mapitem,crop=False,black=False,blendmont=True):
#%%
  # processes a map item and merges the mosaic using IMOD
  # generates a dictionary with metadata for this procedure
  # if crop is selected, a 3dmod session will be opened and the user needs to draw a model of the desired region. The script continues after saving the model file and closing 3dmod.
  # black option will fill the empty spaces between tiles with 0
  # blendmont will use blendmont to merge the montage. If disabled individual tile information is stored in the merge dict nevertheless.

  
  m=dict()
  m['Sloppy'] = False

  # extract map properties
  
  mat = map_matrix(mapitem)
  
  #find map file
  mapfile = map_file(mapitem)
  print('processing mapitem '+mapitem['# Item']+' - file: '+mapfile)
  mapsection = list(map(int,mapitem['MapSection']))[0]

  m['frames'] = list(map(int,mapitem['MapFramesXY']))
  montage_tiles = numpy.prod(m['frames'])
  
  tileidx_offset = 0
  mbase = os.path.splitext(os.path.basename(mapfile))[0]
  
  if mapfile.find('.st')<0 and mapfile.find('.map')<0 and mapfile.find('.mrc')<0:
    #not an mrc file
   
    mergeheader = {}
    mergeheader['stacksize'] = 1
    
    if '.idoc' in mapfile:
        # List of tif files with additional metadata
        
        idoctxt=loadtext(mapfile)       
        
        tilepos=list()
        tilepx=list()
        tilepx1=list()
        
        # find the stack size from the last index of the file list (idoc)
        
        testlast = idoctxt.copy()
        testlast.reverse()
        
        for index,item in enumerate(testlast):
            if item.strip()=='':
                lastitem = testlast[index-1]
                if 'Image = ' in lastitem:
                    break
        
        prefix = mbase[:mbase.find('.idoc')]
        stacksize = int(lastitem[lastitem.find(prefix)+len(prefix):-5])+1            
        mergeheader['stacksize'] = stacksize        
        
        maphead0 = mdoc_item(idoctxt,[],header=True)
        im = list()
        for i in range(0,numpy.min([montage_tiles,stacksize])):            
            tilefile = mapfile[:mapfile.find('.idoc')]+'{:04d}'.format(mapsection + i)+'.tif'
            im.append(tilefile)
            tile = mdoc_item(idoctxt,'Image = '+os.path.basename(tilefile))                            
            tilepos.append(tile['StagePosition'])
            tilepx1.append(tile['PieceCoordinates'])
            
            if 'AlignedPieceCoordsVS' in tile:
                m['Sloppy'] = True
                tilepx.append(tile['AlignedPieceCoordsVS'])
            else:
                tilepx.append(tile['AlignedPieceCoords'])                
                
        if mdoc_item(idoctxt,'MontSection = 0') == []: #older mdoc file format, created before SerialEM 3.7x
            print('Warning - item'+mapitem['# Item']+': Series of tif images without montage information. Assume pixel size is consistent for all sections.')
            
            pixelsize = float(maphead0['PixelSpacing'][0])/ 10000  # in um
            
        else:
            mont_item = mdoc_item(idoctxt,'MontSection = '+str(mapsection))
            pixelsize = float(mont_item['PixelSpacing'][0])/ 10000 # in um
                 
        mergeheader['pixelsize'] = pixelsize
        mapheader = mergeheader.copy()
        mapheader['ysize'] = int(maphead0['ImageSize'][1])
        mapheader['xsize'] = int(maphead0['ImageSize'][0])
        
        imsz_x = int(maphead0['ImageSize'][0])        
        imsz_y = int(maphead0['ImageSize'][1])   
        
        overlapx = imsz_x - mapheader['xsize']
        overlapy = imsz_y - mapheader['ysize'] 
        
        # check if idoc is supported in IMOD (blendmont)
        imod_vercheck = (imod_ver[0]>=4 and imod_ver[1]>=10 and imod_ver[2]>=42)

        if blendmont:
            mergebase = mbase + '_merged'+ '_s' + str(mapsection)
            mergefile = mergebase+'.mrc'
            if not os.path.exists(mergefile):                
                if imod_vercheck:
                    call_blendmont(mapfile,mergebase,mapsection)
                    merge_mrc =  mrc.mmap(mergefile, permissive = 'True')
                    im = merge_mrc.data
                    mergeheader = map_header(merge_mrc)
                else:
                    print('Please update IMOD to > 4.10.42 for merging idoc montages!')                   
                    mergeheader['xsize'] = int(tilepx[-1][0]) + mapheader['xsize']
                    mergeheader['ysize'] = int(tilepx[-1][1]) + mapheader['ysize']
                    mergefile = mapfile
            else:
                merge_mrc =  mrc.mmap(mergefile, permissive = 'True')
                im = merge_mrc.data
                mergeheader = map_header(merge_mrc)
                           
               
            
        else:            
            mergeheader['xsize'] = int(tilepx[-1][0]) + mapheader['xsize']
            mergeheader['ysize'] = int(tilepx[-1][1]) + mapheader['ysize']
            mergefile = mapfile            
    else:
        print('Warning: ' + mapfile + ' is not an MRC file!' + '\n')        
        print('Assuming it is a single tif file or a stitched montage.' + '\n')
        mergefile = mapfile
        pixelsize = 1./numpy.sqrt(abs(numpy.linalg.det(mat))) 
        mergeheader['stacksize'] = 0
        tilepos = mapitem['StageXYZ'][0:2]   
        tilepx = '0'
        tilepx=numpy.array([[tilepx,tilepx,tilepx],[tilepx,tilepx,tilepx]])
        tilepx1 = tilepx
        m['Sloppy'] = 'NoMont'
        im = io.imread(mergefile)
        mergeheader['xsize'] = numpy.array(im.shape)[0]
        mergeheader['ysize'] = numpy.array(im.shape)[1]
        mapheader = mergeheader.copy()
    
    
    mappxcenter = numpy.array([mergeheader['ysize'],mergeheader['xsize']]) / 2     
    

        

  else:
   # map is mrc file
       
    mf = mrc.mmap(mapfile, permissive = 'True')   
    
    mapheader = map_header(mf)
    pixelsize = mapheader['pixelsize']
    mergeheader = mapheader.copy()

    # determine if file contains multiple montages stored in one MRC stack

    mappxcenter = [mapheader['xsize']/2, mapheader['ysize']/2]

    mdocname = mapfile + '.mdoc'    


    if (m['frames'] == [0,0]):
      mapheader['stacksize'] = 0
      tileidx_offset = 0
      tilepos = [0,0]
      if os.path.exists(mdocname):
            mdoclines = loadtext(mdocname)
            pixelsize = float(mdoc_item(mdoclines,'ZValue = '+str(mapsection))['PixelSpacing'][0])/ 10000 # in um
            
    # extract center positions of individual map tiles
    if mapheader['stacksize'] > 1:

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
            tilepx=list()
            tilepx1=list()
            for i in range(0,numpy.min([montage_tiles,mapheader['stacksize']])):
                tile = mdoc_item(mdoclines,'ZValue = ' + str(tileidx_offset+i))                
                tilepos.append(tile['StagePosition'])
                tilepx1.append(tile['PieceCoordinates'])
                
                if 'AlignedPieceCoordsVS' in tile:
                    m['Sloppy'] = True
                    tilepx.append(tile['AlignedPieceCoordsVS'])
                else:
                    tilepx.append(tile['AlignedPieceCoords'])

            
            if mdoc_item(mdoclines,'MontSection = 0') == []: #older mdoc file format, created before SerialEM 3.7x
                print('Warning: mrc stack without montage information. Assume pixel size is consistent for all sections.')
                str1=mdoclines[0]
                pixelsize = float(mdoclines[0][str1.find('=')+1:])
            else:
                mont_item = mdoc_item(mdoclines,'MontSection = '+str(mapsection))
                pixelsize = float(mont_item['PixelSpacing'][0])/ 10000 # in um
                
                
                
           # rotation = float(mdoc_item(mdoclines,'ZValue = '+str(mapsection))['RotationAngle'][0])


        else:
            if mapheader['stacksize'] > montage_tiles:
                    print('WARNING: Multiple maps stored in an MRC stack without mdoc file for metadata. I will guess the pixel size.')
            
            pixelsize = 1./numpy.sqrt(abs(numpy.linalg.det(mat)))
            callcmd = 'extracttilts ' + mapfile + ' -stage -all'
            os.system(callcmd)
            p2 = Popen(callcmd, shell=True, stdout=PIPE)
            o1=list()
            for line in p2.stdout:
                o1.append(line)
                
            tilepos1 = o1[20:-1]
            tilepos = numpy.array([numpy.fromstring(tilepos1[0],dtype=float,sep=' '),numpy.fromstring(tilepos1[1],dtype=float,sep=' ')])
            for item in tilepos1[2:] : tilepos=numpy.append(tilepos,[numpy.fromstring(item,dtype=float,sep=' ')],axis=0)
            blendmont = True
           

    else:
        tilepos1 = list(map(float,mapitem['StageXYZ'][0:2]))
        tilepos = numpy.array([tilepos1,tilepos1])


    # check if map is a montage or not

    

    if mapheader['stacksize'] < 2:
        print('Single image found. No merging needed.')
        tilepx = '0'
        tilepx=numpy.array([[tilepx,tilepx,mapsection],[tilepx,tilepx,mapsection]])
        tilepx1=tilepx
        #os.system(callcmd)
        merge_mrc =  mf
        mergeheader = mapheader.copy()
        overlapx = 0
        overlapy = 0
        tileloc = [0,0]
        imd = merge_mrc.data
        mergefile = mapfile
        
        if len(imd.shape)==3:
            im=imd[mapsection,:,:]
        elif len(imd.shape)==2:
            im=imd

    else:
        if blendmont:
            mergebase = mbase + '_merged'+ '_s' + str(mapsection)
            mergefile = mergebase+'.mrc'
            if not os.path.exists(mergefile):
                call_blendmont(mapfile,mergebase,mapsection,black)
            mergebase = os.path.splitext(mapfile)[0] + '_merged'+ '_s' + str(mapsection)
            mergefile = mergebase + '.mrc'    
            
            merge_mrc =  mrc.mmap(mergefile, permissive = 'True')
            im = merge_mrc.data
            mergeheader = map_header(merge_mrc)            
    
                # extract pixel coordinate of each tile
            tilepx = list(loadtext(mergebase + '.al'))
            for j, item in enumerate(tilepx): tilepx[j] = list(re.split(' +',item))
            
            # use original tile coordinates(pixels) from SerialEM to determine tile position in montage
            tilepx1 = loadtext(mapfile + '.pcs')

            for j, item in enumerate(tilepx1): tilepx1[j] = list(re.split(' +',item))
            merge_mrc.close()            
         
        else:
            mergefile = mapfile
            im = mf.data
            
            mergeheader['xsize'] = int(mapitem['MapWidthHeight'][0])
            mergeheader['ysize'] = int(mapitem['MapWidthHeight'][1])
                         
    im = numpy.rot90(numpy.transpose(im),axes=(0,1))        
    mf.close()    
        # end MRC section
  
  tilepos = numpy.array(tilepos,float)
      
  tilepx = numpy.array(tilepx)
  tilepx = tilepx[tilepx[:,2] == str(mapsection),0:2]
  tilepx = tilepx.astype(numpy.float)    
  
  tilepx1 = numpy.array(tilepx1)
  tilepx1 = tilepx1[tilepx1[:,2] == str(mapsection),0:2]
  tilepx1 = tilepx1.astype(numpy.float)
  
  tpx = tilepx1[:,0]
  tpy = tilepx1[:,1]
  
  if numpy.abs(tpx).max()>0: xstep = tpx[tpx>0].min()
  else: xstep = 1
  if numpy.abs(tpy).max()>0: ystep = tpy[tpy>0].min()
  else: ystep = 1
  
  tileloc = numpy.array([tpx / xstep,tpy/ystep]).T
  
  if not blendmont:
      #prepare coordinate list for Big Stitcher      
      print('preparing coordinate list for BigStitcher for map item '+mapitem['# Item']+'.')
      outpx = tilepx.copy()           
                  
      stitchname = mapfile+'.stitch.csv'
      stitchfile = open(stitchname,'w')
      
      stitchfile.write('dim=2\n')
      #stitchfile.write('ViewSetupID;TimePointID;(position_x, position_y, position_z)\n')                      
      
      for j,item in enumerate(outpx):
          stitchfile.write(str(j)+";;"+"(%s, %s" % (int(item[0]),-int(item[1]))+")\n")
      
      stitchfile.close()
  
  m['sections'] = numpy.array(list(map(int,tileloc[:,0]*m['frames'][1]+tileloc[:,1])))
  
  overlapx = mapheader['xsize'] - xstep
  overlapy = mapheader['ysize'] - ystep
  
      
  # cropping of merged file to only include areas of interest. The user needs to create an IMOD model file and close 3dmod to proceed.
  if crop & blendmont:
      if not os.path.exists(mergebase+'_crop.mrc'):
          loopcount = 0
          print('waiting for crop model to be created ... Please store it under this file name: \"' + mergebase + '.mod\".')
          callcmd = '3dmod \"' +  mergefile + '\" \"' + mergebase + '.mod\"'
          os.system(callcmd)
          while not os.path.exists(mergebase+'.mod'):
              if loopcount > 20: # wait for 6.5 minutes for the model file to be created.
                  print('Timeout - will continue without cropping!')
                  break
              print('waiting for crop model to be created in IMOD... Please store it under this file name: \"' + mergebase + '.mod\".')
              time.sleep(20)
              loopcount = loopcount + 1
              
          if loopcount < 21:
              print('Model file found. Will now generate the cropped map image.')
              callcmd = 'imodmop \"' +  mergebase + '.mod\" \"'+ mergefile + '\" \"' + mergebase + '_crop.mrc\"'
              os.system(callcmd)
              
              merge_mrc.close()
  
      merge_mrc = mrc.mmap(mergebase + '_crop.mrc', permissive = 'True')
      im_cropped = merge_mrc.data
      im_cropped = numpy.rot90(numpy.transpose(im_cropped))
      m['im_cropped'] = im_cropped       
      
  
  mergeheader['pixelsize'] = pixelsize
  mapheader['pixelsize'] = pixelsize

  # generate output
  
  m['mapfile'] = mapfile
  m['mergefile'] = mergefile
  m['matrix'] = mat
  m['tilepos'] = tilepos
  m['im'] = im
  m['mappxcenter'] = mappxcenter
  m['mapheader'] = mapheader
  m['mergeheader'] = mergeheader
  m['tilepx'] = tilepx
  m['tilepx1'] = tilepx1
  m['overlap'] = [overlapx,overlapy]
  m['tileloc'] = tileloc
  m['tileidx_offset'] = tileidx_offset
  
  return m



# -------------------------------
#%%
def call_blendmont(mapfile,mergebase,mapsection,black=False):
    """
    

    Parameters
    ----------
    mapfile : string
        Location of the source map file.
    mergebase : string
        Target file name for merged map (without extension!).
    mapsection : int
        which slice of the stack to process.
    black : TYPE, bool
        whether the background of the merged map hav value 0. The default is False.

    Returns
    -------
    None.

    """
    
    
    # check IMOD version
    if imod_ver[0]<4 | imod_ver[1]<10 | imod_ver[2]<29 :
        print('ERROR: IMOD version needs to be > 4.10.29! Please update. Exiting' + '\n')
        sys.exit(1)
    
    # merge the montage to a single file
    callcmd = 'extractpieces ' +  '\"' + mapfile + '\" \"'  +  mapfile + '.pcs\"'
    os.system(callcmd)
    # print(callcmd)
    
    print('----------------------------------------------------\n')
    print('Merging the map montage into a single image....' + '\n')
    print('----------------------------------------------------\n')
    
    callcmd = 'blendmont -imi ' + '\"' + mapfile + '\"' + ' -imo \"' + mergebase + '.mrc\" -pli \"' + mapfile + '.pcs\" -roo \"' + mergebase  + '.mrc\" -se ' + str(mapsection) + ' -al \"'+ mergebase + '.al\" -sloppy -nofft '    #os.system(callcmd)
    if black:
        callcmd = callcmd + ' -fill 0'
    
    os.system(callcmd)
                
                
                

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
          mapitem = list(filter(lambda c_item:c_item['MapID']==item['SamePosId'],allitems))[0]
          result = realign_map(mapitem)
    else:
      mapID = item['DrawnID']

  else:

    if not 'RealignedID' in item.keys():
      print('No map found to realign item '+ item['# Item'] + ' to, skipping it...')
      result=[]
    else:
      mapID = item['RealignedID']

  result = list(filter(lambda item:item['MapID']==mapID,allitems))

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
  # converts a binary image into a polygon (list of points) describing its outline
  # parameters: image, n of polygon, center around which to draw the polygon, maximum radius of polygon

  # define threshold based on image type
  if img.dtype.kind is 'b':
    thresh = 1
  elif img.dtype.kind is 'i':
    thresh = 2**(8*img.dtype.itemsize-1)-1
    if img.max()<thresh:
        thresh = img.max()/2
  else: thresh = img.max()/2

  # close the polygon
  n_poly = n_poly + 1

  xs , ys = img.shape

  polypt = numpy.empty((0,2))

  # draw equi-angular lines from the center to determine the intersection with the binary image
  polyphi = numpy.linspace(0,2*numpy.pi,n_poly)
  endpts = pol2cart(radius,polyphi)
  endpts = numpy.array(center) + endpts
  
  # find the intersection points and mark the coordinates
  for pt in endpts:
    x, y = numpy.linspace(center[0], pt[0] , radius), numpy.linspace(center[1], pt[1], radius)
    a, b = x.astype(numpy.int),y.astype(numpy.int)
    a[a>(ys-1)] = ys-1
    a[a<0] = 0
    b[b>(xs-1)] = xs-1
    b[b<0] = 0
    lpx = img[b,a].astype(int)
    lpd = numpy.diff(lpx)
    maxdiff = numpy.max(numpy.abs(lpd))
    maxdiff_ix = numpy.argmax(numpy.abs(lpd))
    if maxdiff < thresh:
      maxdiff_ix = radius-1

    polypt = numpy.append(polypt,[(a[maxdiff_ix],b[maxdiff_ix])],axis=0)
     
    
  return polypt

# --------------------------------------

def map_extract(im,c,p,px_scale,t_size,mat,int8=False):
# extracts an image from a given position in an existing map and links positions inside
  imsz1 = t_size * px_scale
 
  # extract image (1.42x to enable rotation)
  cropsize1 = imsz1 * 1.42
  
  cropsize = numpy.array([cropsize1.max(),cropsize1.max()])

  im1 = imcrop(im,c,cropsize)
  
  realsize = numpy.array(im1.shape)

  # center to origin
  p1 = p - c

  # create homogenous matrices
  mat_i = numpy.linalg.inv(mat)
  
  M = numpy.concatenate((mat_i,numpy.array([[0],[0]])),axis=1)
  M = numpy.concatenate((M,[[0,0,1]]),axis=0)
  
  mat1 = numpy.eye(3)
  mat1[0,2] = -(t_size[1]-1)/2
  mat1[1,2] = -(t_size[0]-1)/2
  
  mat2 = numpy.eye(3)
  mat2[0,2] = (realsize[1]-1)/2
  mat2[1,2] = (realsize[0]-1)/2
  
  M1 = numpy.dot(mat2,M)
  M2 = numpy.dot(M1,mat1)
  
  if int8:
     im1 = numpy.round(255.0 * (im1 - im1.min()) / (im1.max() - im1.min() - 1.0)).astype(numpy.uint8) 
    
    # interpolate image
  im2 = tf.warp(im1,M2,output_shape=t_size,preserve_range=True)
  
  #check if output image size needs to be modified
  
  limitsize = numpy.min([[realsize/px_scale],[t_size]],axis=0).squeeze()
  
  
  if (limitsize==t_size).all():
      im3=im2.copy()
      shift = [0,0]
  else:
      # determine limitation of image by the borders of rotated crop
      rotmat=mat/numpy.linalg.det(mat)
      limits=1-abs(numpy.mean([-rotmat[0,1],rotmat[1,0]]))
      outsize = numpy.min([[realsize/px_scale],[t_size]],axis=0).squeeze()*limits
      
      
      # make sure map size matches the original minimum camera pixel block limits (powers of 2)
      ii=1
      while (numpy.mod(t_size,2**ii)==0).all() and ii<4:
          ii=ii+1
      
      shift =   numpy.mod(outsize,2**ii)/2
      outsize = 2**ii*numpy.floor(outsize/(2**ii))
      
      im3 = imcrop(im2,[t_size[1]/2+shift[1],t_size[0]/2+shift[0]],outsize)
      
      im3[im3==0]=numpy.mean(im3[:])
      
  f_size = im3.shape    
      
  if int8:
      im3=im3.astype(numpy.int8)
  else:
      im3=im3.astype(numpy.int16)
  
  p4 = p1 * mat.T

  p4[:,0] =  f_size[1]/2 + p4[:,0]
  p4[:,1] =  f_size[0]/2 + p4[:,1]
  
  

  return im3, p4




# --------------------------------------

def get_pixel(navitem,mergedmap,tile=False,outline=False):
# determines the pixel coordinates of a navigator item in its associated map. 
# input:
# - navigator item
# - map item as resulting from mergemap
# - tile(optional) output is pixel and tile index of closest map tile
# - outline(optional) return coordinates of outline (map/polygon) instead of center point    
# output: pixel coordinates    
    
  
  xval = float(navitem['StageXYZ'][0]) #(float(acq_item['PtsX'][0]))
  yval = float(navitem['StageXYZ'][1]) #(float(acq_item['PtsY'][0]))
  
  pt0 = numpy.array([xval,yval])
  
  pt = pt0.copy()
  # calculate the pixel coordinates
  
  imsz = [mergedmap['mergeheader']['ysize'],mergedmap['mergeheader']['xsize']]
  
  
  if outline:  
    xval1 = numpy.array(navitem['PtsX']).astype(float)
    yval1 = numpy.array(navitem['PtsY']).astype(float)
  
    pt = numpy.vstack((xval1,yval1)).T 
      
  
  if 'XYinPc' in navitem:
    tileid = int(navitem['PieceOn'][0])
    pt_px0 = list(map(float,navitem['XYinPc']))
    pt_px = numpy.array(pt_px0)
    pt_px = numpy.reshape(pt_px,(1,2))
    tileidx = numpy.argwhere(mergedmap['sections']==tileid)[0][0]
    
  else:
         
    tilepos = mergedmap['tilepos']
    
    if (numpy.diff(tilepos,axis=0)[0].max() == 0) and (type(mergedmap['Sloppy']) == bool) and (mergedmap['mapheader']['stacksize'] > 1):
      print('Montage created using image shift! Problems in identifying the positions of clicked points accurately possible!')
	
       
    if len(tilepos.shape)<2:
      tileidx = 0
    else:
      if 'PieceOn' in navitem:
          tileid = int(navitem['PieceOn'][0])
          tileidx = numpy.argwhere(mergedmap['sections']==tileid)[0][0]
      else:
          #TODO   this points to the lower left corner of the tiles NOT to the center!!! ISSUE #2
          tiledist = numpy.sum((tilepos-pt0)**2,axis=1)
          tileidx = numpy.argmin(tiledist)


    # normalize coordinates
    
    ptn = numpy.array(pt - tilepos[tileidx])

    pt_px = numpy.array(ptn*mergedmap['matrix'].T)
    pt_px[:,0] = (mergedmap['mappxcenter'][0]) + pt_px[:,0]
    pt_px[:,1] = (mergedmap['mappxcenter'][1]) - pt_px[:,1]
 
   # output   
  if (not outline):      
      pt_px = pt_px.squeeze()
   
  if tile:
      return (pt_px,tileidx)
  else:
      pt_px1 = pt_px + mergedmap['tilepx'][tileidx]
      pt_px1[1] = imsz[0] - pt_px1[1]
      return pt_px1
   
# ------------------------------------------------------------
  
  
    
def pts2nav(im,pts,cntrs,curr_map,targetitem,nav,sloppy=False,maps=False):
# takes pixel coordinates on an input map, generates virtual maps at their positions, creates polygons matching their shape.
# input parameters:
# - im, original image for feature detection
# - pts, image coordinates, list of arrays (for polygons)
# - cntrs, center of the feature (bounding box)
# - curr_map, map item to process (emtools dict)
# - targetitem, target map
# - nav, all navigator items (emtools dict)
# - sloppy (optional) if merging of original map was sloppy
# - maps (optional) if the virtual maps instead of the points/polygons should be selected for acquisition


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
    
  merge = mergemap(curr_map)

  #mapfile = merge['mapfile']
  #map_mrc = mrc.mmap(mapfile, permissive = 'True')
  mapheader = merge['mapheader']

  pixelsize = mapheader['pixelsize']

  imsz = numpy.array(im.shape)

  map_mat = merge['matrix']

  # target reference

  targetfile = map_file(targetitem)
  target_mrc = mrc.mmap(targetfile, permissive = 'True')
  targetheader = map_header(target_mrc)
  
  
  t_mat = map_matrix(targetitem)


  # combine rotation matrices
  maptf = (numpy.linalg.inv(map_mat) * t_mat).T

  px_scale = targetheader['pixelsize'] /pixelsize

  imsz1 = numpy.array([targetheader['ysize'],targetheader['xsize']])

  ntotal = len(cntrs)

  outnav.append(curr_map)

  curr_id = int(curr_map['MapID'][0])

  delim = 100000

  startid = newID(nav,divmod(curr_id,delim)[0]*delim)

  mapid = startid + 1
  idx=0

  for c in cntrs:

    polynav=dict()
    newnavitem = dict(targetitem)
    mapid = newID(nav,mapid+1)

    print('Processing object '+ str(idx+1) + '/' + str(ntotal) + ' (%2.0f%%)' %(idx*100/ntotal) + ' at position %5u , %5u' %(c[0],c[1]))

    p = pts[idx]

    im4, p4 = map_extract(im,c,p,px_scale,imsz1,maptf)

    
    if min(im4.shape) < 400:
      print('Item is too close to border of map, skipping it.')
      ntotal = ntotal - 1
      continue
    
    p4[:,1] = imsz1[0] - p4[:,1]

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
    
    imfile = 'virt_' + label + '.mrc'

    if os.path.exists(imfile): os.remove(imfile)
    
    im5 = numpy.rot90(im4,3)

    with mrc.new(imfile) as mrcf:
        mrcf.set_data(im5.T)
        mrcf.close()# 
    
    #  map corner points


    cx = imsz1[1]
    cy = imsz1[0]

    a = [[0,0],[cx,0],[cx,cy],[0,cy],[0,0]]
    a = numpy.matrix(a) - [cx/2 , cy/2]
    
    t_mat_i = numpy.linalg.inv(maptf)

    c1 = a*t_mat_i
    
    c_out = c.copy()
    c_out[1] = imsz[0] - c_out[1]

   # c1 = c1 + [c_out[0],c_out[1]]


    
    # fill navigator

    # map for realignment

    newnavitem['MapFile'] = [imfile]
    newnavitem.pop('StageXYZ','')
    newnavitem.pop('RawStageXY','')
    if curr_map['MapFramesXY'] == ['0', '0']:
        newnavitem['CoordsInMap'] = [str(c_out[0]),str(c_out[1]),curr_map['StageXYZ'][2]]
   
    else:
      #  newnavitem['CoordsInAliMont'] = [str(c_out[0]),str(c_out[1]),curr_map['StageXYZ'][2]]
      #  convert aligned pixel coordinates into piece coordinates to ensure map has a proper bounding box
      
      tilecenters = merge['tilepx']+numpy.array([merge['mapheader']['xsize']/2,merge['mapheader']['ysize']/2])
      tiledist = numpy.sum((tilecenters-c_out)**2,axis=1)
      tileidx = numpy.argmin(tiledist)
      c_out = c_out - merge['tilepx'][tileidx]
      c1 = numpy.fliplr(c1 + c_out)
      newnavitem['CoordsInPiece'] = [str(c_out[0]),str(c_out[1]),curr_map['StageXYZ'][2]]
      newnavitem['PieceOn'] = [str(merge['sections'][tileidx])]
        
    cnx = numpy.array(numpy.transpose(c1[:,1]))
    cnx = numpy.array2string(cnx,separator=' ')
    cnx = cnx[2:-2]

    cny = numpy.array(numpy.transpose(c1[:,0]))
    cny = numpy.array2string(cny,separator=' ')
    cny = cny[2:-2]

    newnavitem['PtsX'] = cnx.split()
    newnavitem['PtsY'] = cny.split()
    newnavitem['Note'] = newnavitem['MapFile']
    newnavitem['MapID'] = [str(mapid)]
    newnavitem['DrawnID'] = curr_map['MapID']
    
    if maps:
        newnavitem['Acquire'] = ['1']
    else:
        newnavitem['Acquire'] = ['0']
                
    newnavitem['MapSection'] = ['0']
    newnavitem.pop('SamePosId','')
    # newnavitem['MapWidthHeight'] = [str(im2size[0]),str(im2size[1])]
    newnavitem['ImageType'] = ['0']
    newnavitem['MapMinMaxScale'] = [str(numpy.min(im4)),str(numpy.max(im4))]
    newnavitem['NumPts'] = ['5']
    newnavitem['# Item'] = 'm_' + label
    newnavitem['GroupID'] = [str(newID(nav,startid+50000))]
    curr_map['Acquire'] = ['0']

    # Polygon
    nav_maps.append(newnavitem)  
                
    #do not export points/polygons when maps are inteded output.
        
    if not maps:
        polynav['# Item'] = label
        polynav['Acquire'] = ['1']      
        
        polynav['Draw'] = ['1']
        polynav['Regis'] = curr_map['Regis']
        polynav['DrawnID'] = [str(mapid)]
        polynav['CoordsInMap'] = [str(int(cx/2)) , str(int(cy/2)),curr_map['StageXYZ'][2]]
        polynav['PtsX'] = px.split()
        polynav['PtsY'] = py.split()
        polynav['GroupID'] = [str(newID(nav,startid+70000))]
    
        
    
        nav_pol.append(polynav)



  outnav.extend(nav_maps)
  outnav.extend(nav_pol)



  return outnav



# ------------------------------------------------------------
  
def nav_find(allitems,key,val=[]):
# returns the navigator/mdoc entries with the given key/value pair
# takes an input navigator (list of dicts), a target key (item property) and the desired values to match    
# output is the list of navigator items    
         
    filtered = list(filter(lambda item:item.get(key),allitems))
    
    if val==[]:
        found = filtered
    else:
        # deals with integer, string or list entries
        if type(val)==int: val=str(val)
        if not key == '# Item':
            if type(val)==str: val=[val]
        
        found = list(filter(lambda item:item[key]==val,filtered))
           

    if not found == []:
        newnav=found
    else:
        newnav=[]           
        
        
    
    return newnav

# ------------------------------------------------------------

def nav_selection(allitems,sel=[],acquire=True,maps=False):
    
# extracts a selection of navigator items into a new navigator
# takes an input navigator (list of dicts), an optional list of item labels (one line each) and optional whether to include items selected for acquisition, optionally, all maps the selected points were clicked on are also returned
# if only the input nav is given, it will extract all "Acquire" items
# output is list of navigator items
        
    newnav = list()
    select = sel[:]
    
    if acquire:
        newnav = nav_find(allitems,'Acquire','1')       
        
        
    if not (select == []):
        if  isinstance(select,str):select=[select]                                        
        for listitem in select:
            selitem = nav_find(allitems,'# Item',listitem)
            
            newnav.extend(selitem)
    
    if maps:        
        for item in newnav:
            if 'DrawnID'in item.keys():
                drawnmap = nav_find(allitems,'MapID',item['DrawnID'])
                if (nav_find(newnav,'MapID',item['DrawnID'])==[]):
                    newnav.extend(drawnmap)
                    
    return newnav


# ------------------------------------------------------------
    
def outline2mod(im,namebase,z=0,binning=1):

# takes an input image of label outlines (single pixel thickness)
# creates an IMOD model file with these outlines as contours.
# 
    
    filename = namebase+'.txt'
    f = open(filename,'w')    
   
    
    for label in numpy.unique(im[im>0]):
        a = numpy.argwhere(im == label)
        
        # initialize geometrical sorting, working vars
        am = a
        an = a[0,:]
        pt = an
        am=numpy.delete(am,0,0)
        jump = 0
        
        while(am.shape[0]>2):
            # find neighbouring point from remaining ones
            dist = (am[:,0]-pt[0])**2+(am[:,1]-pt[1])**2
            ix = numpy.argmin(dist)
            
            if numpy.min(dist) > 50:                
                if jump:
                    an = numpy.vstack((an,anchor))
                    pt = anchor
                    jump = 0                    
                else:    
                    anchor = pt
                    jump = 1
                    an = numpy.vstack((an,am[ix,:]))
                    pt = am[ix,:]
                    am=numpy.delete(am,ix,0)
            else:            
                # add to sorted list
                an = numpy.vstack((an,am[ix,:]))
                pt = am[ix,:]
            
            
                # remove this point from input
                am=numpy.delete(am,ix,0)
        
        # add last 2 points to sorted list
        ix = numpy.argmin((am[:,0]-pt[0])**2+(am[:,1]-pt[1])**2)
        an = numpy.vstack((an,am[ix,:]))        
        am = numpy.delete(am,ix,0)
        an = numpy.vstack((an,am[0,:]))      
        
        
        points = numpy.vstack((an[:,1],im.shape[0]-an[:,0])).transpose() * binning
        
        
        # write output file        
        for j,item in enumerate(points):
            f.write(" 1  "+str(label)+"  %s %s" % (item[0],item[1])+" "+str(z)+"\n")
            
    
    
    f.close()
    
    #convert into IMOD model
    callcmd = 'point2model \"'+filename+'\" \"'+namebase+'.mod\"'
    os.system(callcmd)
    
    
    
    
# ------------------------------------------------------------ 
        
def ordernav(nav,delim=''):
# re-orders a navigator by its label.
# It considers the indexing after a delimiter in the string.
# example: s01_cell-1,s02_cell-1,s01_cell-02, ...    is sorted by cells instead of s...
# when no delimiter is given, the navigator is sorted by its label.
    
    nav1=nav.copy()

    non_idx = 0
    
    for item in nav1: 
        if delim=='' :
            item['# Sorting'] = item['# Item']
                
        elif item['# Item'].find(delim) == -1:
            item['# Sorting'] = str(non_idx).zfill(5)
            non_idx = non_idx+1
        else:
            item['# Sorting'] = item['# Item'][item['# Item'].find(delim)+1:]
    
    newnav = sorted(nav1.copy(),key = itemgetter('# Sorting'))
                                         
    for item in newnav: 
        item.pop('# Sorting')

    
    return newnav
        
# ------------------------------------------------------------ 
        
def pointitem(label,regis=1):
# creates a default point item containing all necessary item parameters.
# The corresponding MapID and Position need to be defined externally!
    
    point=dict()
    point['# Item'] = label
    point['Color'] = ['0']
    
    if type(regis)==list:
        regis=''.join(regis)
    
    point['Regis'] = [str(regis)]
    point['NumPts'] = ['1']
    point['Type'] = ['0']    
    
    return point
    
    
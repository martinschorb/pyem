# -*- coding: utf-8 -*-

from pandas import DataFrame
from KNIPImage import KNIPImage

import sys
import os
import numpy
from scipy.ndimage.interpolation import zoom
from skimage.measure import regionprops
import tifffile as tiff

sys.path.append('/g/emcf/schorb/code/python')

import emtools as em

reload(em)

# Create empty table
output_table_1 = DataFrame()
output_table_2 = DataFrame()

out=list()

navlines_input = input_table_2['navlines']
navlines = map(str,navlines_input.tolist())

targetitem = em.nav_item(navlines,flow_variables['target_map'])


allitems = em.fullnav(navlines)
nav=allitems

navname = flow_variables['navfile']


newnav = navname[:-4] + '_automaps.nav'
nnf = open(newnav,'w')
nnf.write("%s\n" % navlines[0])
nnf.write("%s\n" % navlines[1])


navfile=flow_variables['navfile']
os.chdir(navfile[:navfile.rindex('/')+1])

targetfile = em.map_file(targetitem)
targetheader = em.map_header(targetfile)

tx = map(float,targetitem['PtsX'])
ty = map(float,targetitem['PtsY'])

targetrot = em.map_rotation(tx,ty)

binning = flow_variables['bin']

midx = 1


# Loop over every cell in the 'Img' column
for index,input_cell in input_table_1['Labels'].iteritems():

	# get image from cell
	img = input_cell.array

	a = regionprops(img)

	polys = list()
	centers = list()

	mapid = "_{0}".format(midx)

	orig = tiff.imread(flow_variables['mapfile'+mapid])
	imsize = numpy.array(orig.shape)
	curr_map = em.nav_item(navlines,flow_variables['map'+mapid])
	pixelsize = flow_variables['map_px'+mapid]


	mx = map(float,curr_map['PtsX'])
	my = map(float,curr_map['PtsY'])

	maprot = em.map_rotation(tx,ty)


	midx = midx + 1

	for label in a[0:10]:
		s = label.image
		bb = numpy.array(label.bbox)
		p = em.img2polygon(s,12,label.local_centroid, numpy.max(s.shape))
		p[:,0] = p[:,0]+bb[1]
		p[:,1] = p[:,1]+bb[0]
		p = p*binning
		polys.append(p)

		c = [(bb[1]+(bb[3]-bb[1])/2)*binning, (bb[0]+(bb[2]-bb[0])/2)*binning]
		centers.append(c)

	outnav = em.pts2nav(orig,polys,centers,curr_map,targetitem,nav)

	for nitem in outnav:
  		out.extend(em.itemtonav(nitem,nitem['# Item']))

for item in out: nnf.write("%s\n" % item)


nnf.close()

print('Done processing '+navname)

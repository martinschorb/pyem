# -*- coding: utf-8 -*-

from skimage.measure import regionprops


(img,targetitem,mapitem,allitems,navfile,binning)



newnav = navfile[:-4] + '_automaps.nav'
nnf = open(newnav,'w')
nnf.write("%s\n" % navlines[0])
nnf.write("%s\n" % navlines[1])

targetfile = map_file(targetitem)
targetheader = map_header(targetfile)

targetrot = map_rotation(tx,ty)


a = regionprops(img)

polys = list()
centers = list()

mmap = mergemap(mapitem)

orig = mmap[im]

imsize = numpy.array(orig.shape)
curr_map = mapitem

pixelsize = mmap['pixelsize']

mx = map(float,curr_map['PtsX'])
my = map(float,curr_map['PtsY'])

maprot = map_rotation(mx,my)

for label in a:
   s = label.image
   bb = numpy.array(label.bbox)
   p = img2polygon(s,12,label.local_centroid, numpy.max(s.shape))
   p[:,0] = p[:,0]+bb[1]
   p[:,1] = p[:,1]+bb[0]
   p = p*binning
   polys.append(p)

   c = [(bb[1]+(bb[3]-bb[1])/2)*binning, (bb[0]+(bb[2]-bb[0])/2)*binning]
   centers.append(c)


outnav = pts2nav(orig,polys,centers,curr_map,targetitem,nav)

for nitem in outnav:
	 out.extend(em.itemtonav(nitem,nitem['# Item']))

for item in out: nnf.write("%s\n" % item)

nnf.close()

print('Done processing '+navname)

# -*- coding: utf-8 -*-

# maps_acquire.py - (C) 2018 Martin Schorb EMBL
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


# dependencies

import os
import sys

import pyEM as em

# PARAMETERS

navname = sys.argv[1]
# file name navigator

# change path to working directory
os.chdir(os.path.dirname(navname))

view_map = 'view'  # map'
# one example map at the desired settings (View) (NavLabel)

preview_map = 'preview'  # map'
# one example map at the desired settings (Preview) (NavLabel)


# ====================================================================================
# %%

# start script


navlines = em.loadtext(navname)
(targetitem, junk) = em.nav_item(navlines, view_map)

newnavf = navname[:-4] + '_automaps.nav'
# nnf = open(newnavf,'w')
# nnf.write("%s\n" % navlines[0])
# nnf.write("%s\n\n" % navlines[1])


allitems = em.fullnav(navlines)

acq = filter(lambda item: item.get('Acquire'), allitems)
acq = list(filter(lambda item: item['Acquire'] == ['1'], acq))

non_acq = [x for x in allitems if x not in acq]

non_acq.remove(targetitem)

maps = {'mapnav': []}

newmapid = em.newID(allitems, 10000)

outnav1 = list()
ntotal = len(acq)

(viewitem, junk) = em.nav_item(navlines, view_map)
if viewitem == []:
    raise Exception('ERROR!  No reference map with label "' + view_map + '" specified!')

(previewitem, junk) = em.nav_item(navlines, preview_map)
if previewitem == []:
    raise Exception('ERROR!  No reference map with label "' + preview_map + '" specified!')

view_merge = em.mergemap(viewitem)
preview_merge = em.mergemap(previewitem)

v_header = view_merge['mergeheader']
p_header = preview_merge['mergeheader']
# -----
# %%


for idx, acq_item in enumerate(acq):
    print('Processing navitem ' + str(idx + 1) + '/' + str(ntotal) + ' (%2.0f%% done)' % (idx * 100 / ntotal))
    (viewnav, maps, acq_item) = em.virt_map_at_point(acq_item, idx, maps, allitems, viewitem, v_header, outnav1.copy())
    outnav1.append(acq_item)
    if viewnav is not None:
        outnav1.append(viewnav.copy())
    (previewnav, maps, acq_item) = em.virt_map_at_point(acq_item, idx, maps, allitems, previewitem, p_header,
                                                        outnav1.copy())
    if previewnav is not None:
        outnav1.append(previewnav)

# finalnav.sort(key=itemgetter('# Item'))
on1 = em.ordernav(outnav1, delim='_')

finalnav = maps['mapnav'].copy()
finalnav.extend(on1.copy())

em.write_navfile(newnavf, finalnav, xml=False)

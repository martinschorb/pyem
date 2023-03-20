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
# - one mrc file at the desired virtual magnification and image size for each item
# - a new navigator file containing all new maps with acquisition already enabled


# dependencies

import os
import sys

from operator import itemgetter

# import matplotlib.pyplot as plt

import pyEM as em

# ====================================================================================
# %%

# PARAMETERS

navname = sys.argv[1]
# file name navigator

# change path to working directory
os.chdir(os.path.dirname(navname))

target_map = 'refmap'
# one example map at the desired settings (NavLabel)


# ====================================================================================
# %%


# start script


navlines = em.loadtext(navname)
(targetitem, junk) = em.nav_item(navlines, target_map)

if targetitem == []:
    raise Exception('ERROR!  No reference map with label "' + target_map + '" specified!')

target_merge = em.mergemap(targetitem)
targetheader = target_merge['mergeheader']

newnavf = navname[:-4] + '_automaps.nav'
# nnf = open(newnavf,'w')
# nnf.write("%s\n" % navlines[0])
# nnf.write("%s\n" % navlines[1])


allitems = em.fullnav(navlines)

acq = filter(lambda item: item.get('Acquire'), allitems)
acq = list(filter(lambda item: item['Acquire'] == ['1'], acq))

non_acq = [x for x in allitems if x not in acq]

non_acq.remove(targetitem)

maps = {}
maps['mapnav'] = []

newmapid = em.newID(allitems, 10000)

outnav = list()
ntotal = len(acq)

newnav = list()

for idx, acq_item in enumerate(acq):
    print('Processing navitem ' + str(idx + 1) + '/' + str(ntotal) + ' (%2.0f%% done)' % (idx * 100 / ntotal))

    newnavitem, maps, item = em.virt_map_at_point(acq_item, idx, maps, allitems, targetitem, targetheader, outnav,
                                                  outformat='mrc', numtiles=1)

    outnav.append(item)
    outnav.append(newnavitem)

outnav.sort(key=itemgetter('# Item'))

# for nitem in non_acq:
#    newnav.append(nitem)

on1 = em.ordernav(outnav, delim='_')

finalnav = maps['mapnav'].copy()
finalnav.extend(on1.copy())

em.write_navfile(newnavf, finalnav, xml=False)

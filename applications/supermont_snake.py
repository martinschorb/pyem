# -*- coding: utf-8 -*-
# import the py-EM module and make its functions available
import pyEM as em
import numpy as np

# parse command line parameters

# import argparse

# parser = argparse.ArgumentParser(description='Sort navigator file.')
# parser.add_argument('navfile', metavar='navfile', type=str, help='a navigator file location')

# args = parser.parse_args()

# navfile = args.navfile

import sys

navfile = sys.argv[1]

# load the navigator file
navlines = em.loadtext(navfile)
allitems = em.fullnav(navlines)

sm_items = list(filter(lambda item: item.get('SuperMontXY'), allitems))

supermont = []
sm_coos = []

for item in sm_items:
    sm_id = item['# Item'].split('-')
    supermont.append('_'.join(sm_id[0:len(sm_id) - 2]))
    sm_coos.append([int(sm_id[-2]), int(sm_id[-1])])

smcoos = np.array(sm_coos)
smitems = np.array(sm_items)

out_sm = []

for sm in np.unique(supermont):
    out_sm0 = []
    thiscoos = smcoos[np.where(np.array(supermont) == sm)]
    thisitems = smitems[np.where(np.array(supermont) == sm)]
    sm_range = np.max(thiscoos, 0) - np.min(thiscoos, 0)

    if sm_range[1] < sm_range[0]:
        sortidx0 = np.argsort(thiscoos[:, 1])
        sortidx1 = np.argsort(thiscoos[:, 0], kind='mergesort')
        thiscoos = np.fliplr(thiscoos[sortidx1])
        thisitems = thisitems[sortidx1]

    templist = []

    for idx, leg in enumerate(thiscoos):
        print('checking tile ' + str(idx + 1) + '...')
        if np.divmod(leg[1], 2)[1] > 0:
            templist.reverse()
            out_sm0.extend(templist)
            templist = []
            out_sm0.append(thisitems[idx])
        else:
            templist.append(thisitems[idx])

    route_polyX = []
    route_polyY = []

    for item in out_sm0:
        current = sm_items.index(next(filter(lambda itm: itm['# Item'] == item['# Item'], sm_items)))
        route_polyX.append(sm_items[current]['StageXYZ'][0])
        route_polyY.append(sm_items[current]['StageXYZ'][1])

    poly = em.pointitem('SM_' + str(sm) + '_start')
    poly['Type'] = '1'  # polygon
    poly['StageXYZ'] = thisitems[0]['StageXYZ']
    poly['NumPts'] = [str(len(out_sm0))]
    poly['PtsX'] = route_polyX
    poly['PtsY'] = route_polyY

    out_sm.extend(out_sm0)

    out_sm.append(poly)

non_sm = [x for x in allitems if x not in sm_items]
# newnav = non_acq

# create new file by copying the header of the input file
newnavf = navfile[:-4] + '_snake.nav'

outnav = list()
#
# nnf = open(newnavf,'w')
# nnf.write("%s\n" % navlines[0])
# nnf.write("%s\n" % navlines[1])

# fill the new file
outnav.extend(non_sm)
outnav.extend(out_sm)

print('----------------------------------------\n Done.\n Writing output Supermontage as ' + newnavf + '.')

em.write_navfile(newnavf, outnav, xml=False)

# -*- coding: utf-8 -*-
# import the py-EM module and make its functions available
import pyEM as em
import numpy as np

# parse command line parameters

#import argparse

#parser = argparse.ArgumentParser(description='Sort navigator file.')
#parser.add_argument('navfile', metavar='navfile', type=str, help='a navigator file location')

#args = parser.parse_args()

#navfile = args.navfile

import sys

navfile = sys.argv[1]


def neighbours(inarr,pt,dist=1):
    i_range = np.linspace(-dist,dist,2*dist+1)
    p0 = np.repeat(pt[0]+i_range,len(i_range))
    p1 = np.tile(pt[1]+i_range,len(i_range))
    allnbrs = np.stack([p0,p1],axis=-1)

    eu_dist = np.linalg.norm(allnbrs-pt,axis=1)
    circ = allnbrs[np.argwhere(np.all(np.stack([eu_dist<=dist,eu_dist>(dist-1)],axis=1),axis=1))].squeeze()

    out=[]
    for nb in circ:
        if any(np.all(nb-inarr==[0,0],axis=1)): out.append(nb)

    return np.array(out,dtype=int)


def step(inarr,pt,maxdist=6):
    pt_index = np.argwhere(np.all(inarr-pt==[0,0],axis=1))
    outarr = np.delete(inarr,pt_index,0)
    nbs = []
    dist = 0

    while len(nbs) < 1 and dist < maxdist:
        dist += 1
        nbs = neighbours(outarr,pt,dist=dist)

    if len(nbs)>0:
        outpt = nbs[int(np.random.random() * len(nbs))]
    else:
        outarr=[]
        outpt=[0,0]

    return outarr, outpt, np.linalg.norm(outpt-pt)

def tour(inarr,start,maxdist=6):
    pt = np.copy(start)
    outarr = np.copy(inarr)
    dist=0
    route = [start]

    for leg,tpt in enumerate(inarr):
        outarr,pt,stepdist = step(outarr,pt,maxdist=maxdist)
        if len(outarr) < 1 and leg < len(inarr-1):
            return None,[]
        route.append(pt)
        dist+=stepdist

    return dist,np.array(route)

def randomtour(inarr,numtrials = 20):

    dists = []
    routes = []
    pidx = -1
    start = inarr[0]

    for i in range(numtrials):
        pidx0 = int(i/numtrials*100)
        if pidx0 != pidx:
            print('Searching... - '+str(pidx0)+'% completed.')
            pidx=pidx0

        d = None

        while d is None:
            d, route = tour(inarr, start,maxdist=10)

        routes.append(route)
        dists.append(d)

    return dists,routes

# load the navigator file
navlines = em.loadtext(navfile)
allitems = em.fullnav(navlines)



sm_items = list(filter(lambda item:item.get('SuperMontXY'),allitems))

supermont=[]
sm_coos = []

for item in sm_items:
    sm_id = item['# Item'].split('-')
    supermont.append('_'.join(sm_id[0:len(sm_id)-2]))
    sm_coos.append([int(sm_id[-2]), int(sm_id[-1])])

smcoos = np.array(sm_coos)
smitems = np.array(sm_items)

out_sm = []

for sm in np.unique(supermont):

    thiscoos = smcoos[np.where(np.array(supermont)==sm)]
    thisitems = smitems[np.where(np.array(supermont)==sm)]
    sm_range = np.max(thiscoos, 0) - np.min(thiscoos, 0)




    snakedim = np.argmin(sm_range)

    templist = []

    for idx,leg in enumerate(thiscoos):
        if np.divmod(leg[1],2)[1]>0:
            templist.reverse()
            out_sm.extend(templist)
            templist = []
            out_sm.append(thisitems[idx])
        else:
            templist.append(thisitems[idx])

non_sm = [x for x in allitems if x not in sm_items]
#newnav = non_acq

# create new file by copying the header of the input file
newnavf = navfile[:-4] + '_snake.nav'

outnav = list()
#
#nnf = open(newnavf,'w')
#nnf.write("%s\n" % navlines[0])
#nnf.write("%s\n" % navlines[1])

# fill the new file   
outnav.extend(non_sm)
outnav.extend(out_sm)
    
    
em.write_navfile(newnavf,outnav,xml=False)

    

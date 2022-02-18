# -*- coding: utf-8 -*-
# import the py-EM module and make its functions available
import pyEM as em
import numpy as np
from scipy.cluster.vq import kmeans, whiten
import os
import sys
from functools import partial
if os.name == 'nt':
    from multiprocessing.pool import ThreadPool as Pool
else:
    from multiprocessing import Pool
import tqdm
# parse command line parameters

#import argparse

#parser = argparse.ArgumentParser(description='Sort navigator file.')
#parser.add_argument('navfile', metavar='navfile', type=str, help='a navigator file location')

#args = parser.parse_args()

#navfile = args.navfile





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


def step(inarr,pt,maxdist=6,nb=True):
    pt_index = np.argwhere(np.all(inarr-pt==[0,0],axis=1))
    outarr = np.delete(inarr,pt_index,0)
    nbs = []
    dist = 0
    outpt = [0, 0]
    if nb:
        while len(nbs) < 1 and dist < maxdist:
            dist += 1
            nbs = neighbours(outarr,pt,dist=dist)
        if len(nbs)==0:
            outarr = []
        else:
            outpt = nbs[int(np.random.random() * len(nbs))]
    else:
        if len(outarr)>0:
            outpt = outarr[int(np.random.random() * len(outarr))]

    return outarr, outpt, np.linalg.norm(outpt-pt)


def tour(inarr,start,maxdist=6,nb=True):
    pt = np.copy(start)
    outarr = np.copy(inarr)
    dist=0
    route = [start]
    for leg,tpt in enumerate(inarr):
        outarr,pt,stepdist = step(outarr,pt,maxdist=maxdist,nb=nb)

        if leg < len(inarr)-1:
            if len(outarr) < 1:
                return None, []
            route.append(pt)
            dist+=stepdist
    return dist,np.array(route)



def par_randomtour(pidx0,inarr,start,maxdist,nb=True):
        d = None
        while d is None:
            d, route = tour(inarr, start,maxdist=maxdist,nb=nb)
        return (d,route)


def splitcoos(inarr,size=50):
    n,rem=np.divmod(len(inarr),size)
    n+=1

    whitened = whiten(inarr)
    clusterpts,distortion = kmeans(whitened, n)

    pool = Pool()
    numtrials=100
    par_clustertour = partial(par_randomtour, inarr=clusterpts, start=inarr[0], maxdist=3,
                              nb=False)
    print('Optimizing aquisition subregions.')
    result_list = tqdm.tqdm(pool.imap(par_clustertour, np.linspace(0, 100, numtrials)),total=numtrials)

    dists, routes = zip(*result_list)

    clusterpts = routes[np.argmin(dists)]

    cp_dists = []
    for cp in clusterpts:
        cp_dists.append(list(np.linalg.norm(whitened - cp,axis=1)))

    cluster=np.argmin(np.array(cp_dists),axis=0)

    return cluster


def connectregions(inarr,cluster):
    regions =[]

    for region in np.unique(cluster):
        regions.append(inarr[cluster==region])

    fullroute = []

    r_idx = 0
    nextpoint_ix = np.argmin(np.linalg.norm(regions[r_idx + 1] - np.mean(regions[r_idx], axis=0), axis=1))
    startpoint = regions[r_idx + 1][nextpoint_ix]
    thisregion = np.vstack((regions[r_idx], startpoint))
    # regions[r_idx + 1] = np.delete(regions[r_idx + 1], nextpoint_ix,axis=0)
    numtrials = 20

    pool = Pool()
    par_clustertour = partial(par_randomtour, inarr=thisregion, start=startpoint, maxdist=3)
    print('Processing subregion 1/'+str(len(regions))+'.')
    result_list = tqdm.tqdm(pool.imap(par_clustertour,np.linspace(0,100,numtrials)),total=numtrials)

    dists, routes = zip(*result_list)
    routes = list(map(list, routes))
    dists = list(dists)

    for rt_ix,rt in enumerate(routes):
        routes[rt_ix] = np.flipud(rt)

    fullroute.extend(routes[np.argmin(dists)][:-1])
    numtrials = 200

    for r_idx in range(len(regions)-1):
        pool = Pool()
        par_clustertour = partial(par_randomtour, inarr=regions[r_idx+1], start=startpoint, maxdist=3)
        print('Processing subregion '+str(r_idx+2)+'/'+str(len(regions))+'.')
        result_list = tqdm.tqdm(pool.imap(par_clustertour, np.linspace(0, 100, numtrials)),total=numtrials)

        dists, routes = zip(*result_list)
        routes = list(map(list, routes))
        dists = list(dists)

        stpts=[]
        if r_idx < len(regions) - 2:
            for rt_idx,route in enumerate(routes):
                next_dist = np.linalg.norm(regions[r_idx + 2] - route[-1], axis=1)
                nextpoint_ix = np.argmin(next_dist)
                dists[rt_idx] += np.min(next_dist)
                stpts.append(regions[r_idx + 2][nextpoint_ix])

            startpoint = stpts[np.argmin(dists)]
        fullroute.extend(routes[np.argmin(dists)])

    return np.array(fullroute)


# ===================================================================


def run(navfile):


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

        cluster = splitcoos(thiscoos)
        fullroute = connectregions(thiscoos, cluster)

        route_idx=[]
        route_polyX = []
        route_polyY = []

        for pt in fullroute:
            current = int(np.argwhere(np.all(thiscoos-pt==[0,0],axis=1)))
            route_idx.append(current)

            out_sm.append(sm_items[current])
            route_polyX.append(sm_items[current]['StageXYZ'][0])
            route_polyY.append(sm_items[current]['StageXYZ'][1])

        poly = em.pointitem('SM_'+str(sm)+'_start')
        poly['Type'] = '1' #polygon
        poly['StageXYZ'] = sm_items[route_idx[0]]['StageXYZ']
        poly['NumPts'] = [str(len(fullroute))]
        poly['PtsX'] = route_polyX
        poly['PtsY'] = route_polyY

        out_sm.append(poly)

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

    print('----------------------------------------\n Done.\n Writing output Supermontage as '+newnavf+'.')

    em.write_navfile(newnavf,outnav,xml=False)

if __name__ == '__main__':
    navfile = sys.argv[1]
    run(navfile)
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  2 15:32:11 2019

@author: EMCF
"""



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


# load the navigator file
navlines = em.loadtext(navfile)
allitems = em.fullnav(navlines)

newnavf = navfile[:-4]+'_mapidfix.nav'
nnf = open(newnavf,'w')
nnf.write("%s\n" % navlines[0])
nnf.write("%s\n" % navlines[1])

ntotal = len(allitems)

for idx,item in enumerate(allitems):
    if   item.get('Acquire') == ['1']:
        searchstr = 'm'+item['# Item'][1:]
        mapitems = em.navlabel_match(allitems, searchstr)
        mag = []
        for m in mapitems: mag.append(int(m['MapMagInd'][0]))
        mapitem = mapitems[np.argmax(mag)]
        
        item['DrawnID'] = mapitem['MapID']
        
# fill the new file   
for nitem in allitems: 
    out = em.itemtonav(nitem,nitem['# Item'])
    for item in out: nnf.write("%s\n" % item)
            
    

nnf.close()

      
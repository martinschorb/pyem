# -*- coding: utf-8 -*-
"""
Spyder Editor

Dies ist eine temporäre Skriptdatei.
"""


import pyEM as em

# parse command line parameters

#import argparse

#parser = argparse.ArgumentParser(description='Sort navigator file.')
#parser.add_argument('navfile', metavar='navfile', type=str, help='a navigator file location')

#args = parser.parse_args()

#navfile = args.navfile

target_map = 'refmap'


import sys

navfile = sys.argv[1]


# load the navigator file
navlines = em.loadtext(navfile)
allitems = em.fullnav(navlines)

newnavf = navfile[:-4]+'_updated.nav'
nnf = open(newnavf,'w')
nnf.write("%s\n" % navlines[0])
nnf.write("%s\n" % navlines[1])



(targetitem,junk) = em.nav_item(navlines,target_map)

#targetfile = em.map_file(targetitem)
#target_mrc = mrc.open(targetfile, permissive = 'True')
#targetheader = em.map_header(target_mrc)

#t_mat = em.map_matrix(targetitem)

ntotal = len(allitems)

for idx,item in enumerate(allitems):
  
  if   item.get('Acquire') == ['1']:
    
      print('Processing navitem '+ str(idx+1) + '/' + str(ntotal) + ' (%2.0f%% done)' %(idx*100/ntotal))
      
      item['MapBinning'] = targetitem['MapBinning']
      item['MapSpotSize'] = targetitem['MapSpotSize']
      item['MapMagInd'] = targetitem['MapMagInd']
      item['MapIntensity'] = targetitem['MapIntensity']
      item['MapCamera'] = targetitem['MapCamera']
      item['MapExposure'] = targetitem['MapExposure']
      
      

# fill the new file   
for nitem in allitems: 
    out = em.itemtonav(nitem,nitem['# Item'])
    for item in out: nnf.write("%s\n" % item)
            
    

nnf.close()


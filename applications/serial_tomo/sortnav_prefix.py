# -*- coding: utf-8 -*-
# import the py-EM module and make its functions available
import pyEM as em

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

# create a new list of navigator entries using the ordernav function
newnav = em.ordernav(allitems,'_rs')

# create new file by copying the header of the input file
newnavf = navfile[:-4] + '_sorted.nav'

print('Navigator file was sorted and output is written as: ' + newnavf)

nnf = open(newnavf,'w')
nnf.write("%s\n" % navlines[0])
nnf.write("%s\n" % navlines[1])

# fill the new file   
for nitem in newnav: 
    out = em.itemtonav(nitem,nitem['# Item'])
    for item in out: nnf.write("%s\n" % item)
            
    
    
    
nnf.close()

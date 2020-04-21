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


acq = filter(lambda item:item.get('Acquire'),allitems)
acq = list(filter(lambda item:item['Acquire']==['1'],acq))

non_acq = [x for x in allitems if x not in acq]
newnav = non_acq

# create new file by copying the header of the input file
newnavf = navfile#[:-4] + '_clean.nav'

print('Navigator items marked with Acquire were duplicated and output is written as: ' + newnavf)


em.write_navfile(newnavf,newnav,xml=False)

    
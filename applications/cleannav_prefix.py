# -*- coding: utf-8 -*-
# import the py-EM module and make its functions available
import pyEM as em

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

acq = filter(lambda item: item.get('Acquire'), allitems)
acq = list(filter(lambda item: item['Acquire'] == ['1'], acq))

non_acq = [x for x in allitems if x not in acq]
# newnav = non_acq

# create new file by copying the header of the input file
newnavf = navfile[:-4] + '_clean.nav'

outnav = list()
#
# nnf = open(newnavf,'w')
# nnf.write("%s\n" % navlines[0])
# nnf.write("%s\n" % navlines[1])

# fill the new file   
for item in acq:
    labelstr = item['# Item']
    searchstr = labelstr  # [1:4]
    include = list(filter(lambda item: item['# Item'].find(searchstr) > 0, non_acq))
    for navitem in include:
        outnav.extend(include)

em.write_navfile(newnavf, outnav, xml=False)

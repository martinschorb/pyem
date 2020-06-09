# -*- coding: utf-8 -*-
# import the py-EM module and make its functions available
import pyEM as em

import xml.etree.ElementTree as ET



# parse command line parameters


import sys
import os








def pts2xml(imfile,pts):
    
    xml_out = os.path.splitext(imfile)[0]+'.xml'
        
    root = ET.Element('root')
    
    name = ET.SubElement(root, 'name')
    name.text = os.path.splitext(os.path.basename(imfile))[0]
    
    rois = ET.SubElement(root, 'rois')
    
    ol = ET.SubElement(root, 'overlays')
    
    for pt in pts:
        roi = ET.SubElement(rois, 'roi')
        
        cn = ET.SubElement(roi, 'classname')
        cn.text = 'plugins.kernel.roi.roi3d.ROI3DPoint'
        
        p_id = ET.SubElement(roi, 'id')
        p_id.text = pt[1]
        
        col = ET.SubElement(roi, 'color')
        col.text = '-48641'
        
        sn = ET.SubElement(roi, 'showName')
        sn.text = 'true'       
                
        pname = ET.SubElement(roi, 'name')
        pname.text = 'Point '+ pt[1]
        
        z = ET.SubElement(roi, 'z')
        z.text = '0'
        
        pos = ET.SubElement(roi, 'position')
        x = ET.SubElement(pos, 'pos_x')
        x.text = str(pt[0][0])
        y = ET.SubElement(pos, 'pos_y')
        y.text = str(pt[0][1])

    
    em.indent_xml(root)
    tree = ET.ElementTree(root)
    tree.write(xml_out)







#%%

navfile = sys.argv[1]

#%%


# load the navigator file
navlines = em.loadtext(navfile)
allitems = em.fullnav(navlines)

outitems = list(allitems)



# select "ACQUIRE"
acq = em.nav_selection(allitems)

# check that only two proper maps are selected
if not len(acq) == 2: raise ValueError('Select two maps as items to acquire.')
if not any('Imported' in item.keys() for item in acq):  raise ValueError('One map needs to be imported.')

for item in acq :
    if 'Imported' in item.keys():
        m_fm = item
        mm_fm = em.mergemap(item)
    else:
        m_em = item
        mm_em = em.mergemap(item)

# Find all relevant registration pts

fm_regpts = em.nav_find(allitems,key='DrawnID',val=m_fm['MapID'])
fm_regpts = em.nav_find(fm_regpts,key='RegPt')

fm_px = []
for regpt in fm_regpts:
    fm_px.append([em.get_pixel(regpt,mm_fm),regpt['RegPt'][0]])
    outitems.remove(regpt)

em_regpts = em.nav_find(allitems,key='DrawnID',val=m_em['MapID'])
em_regpts = em.nav_find(em_regpts,key='RegPt')

em_px = []
for regpt in em_regpts:
    em_px.append([em.get_pixel(regpt,mm_em),regpt['RegPt'][0]])
    outitems.remove(regpt)


pts2xml(mm_fm['mapfile'], fm_px)
pts2xml(mm_em['mergefile'], em_px)

# create new file by copying the header of the input file
newnavf = navfile[:-4] + '_icy.nav'

em.write_navfile(newnavf,outitems,xml=False)
    

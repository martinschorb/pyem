# -*- coding: utf-8 -*-
# import the py-EM module and make its functions available
import pyEM as em

import xml.etree.ElementTree as ET



# parse command line parameters


import sys
import os
import glob
import numpy as np






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


##                ICY   runs here      


print('----------------------------------------------------------------')
print('        Starting Icy..................................')
print('----------------------------------------------------------------')
print(' Please run ec-CLEM and when done click SHOW ROIs ON ORIGINAL SOURCE IMAGE\n')


workdir = os.getcwd()

os.chdir('C:\Software\icy')
icycmd = 'java -jar icy.jar -x plugins.tprovoost.scripteditor.main.ScriptEditorPlugin C:\Software\opener.js'

os.system(icycmd +' '+ mm_fm['mapfile'] +' '+  mm_em['mergefile'])

os.chdir(workdir)


#%%

# import icy XMLs

x_emf = mm_em['mergefile']+ os.path.splitext( mm_em['mapfile'])[1] + '_ROIsavedwhenshowonoriginaldata' + '.xml'
x_trafo = mm_fm['mapfile'] + '_transfo' + '.xml'

if not all([os.path.exists(x_emf),os.path.exists(x_trafo)]):  raise ValueError('Could not find the results of Icy registration. Please re-run.')
    
root_em = ET.parse(x_emf)
root_trafo = ET.parse(x_trafo)


# extract transformation matrices

mat = []
if root_trafo.find('MatrixTransformation') == None:
    root_trafo = ET.parse(glob.glob(mm_fm['mapfile'] + '_transfo' + '*back-up.xml')[-1])


for child in root_trafo.iter():
    if child.tag == 'MatrixTransformation':
        mat.append(child.attrib)

M = np.eye(4)
M_list = list()
        
for matrix in mat:
    thismat = np.eye(4)
    thismat[0,0] = matrix['m00']
    thismat[0,1] = matrix['m01']
    thismat[0,2] = matrix['m02']
    thismat[0,3] = matrix['m03']
    thismat[1,0] = matrix['m10']
    thismat[1,1] = matrix['m11']
    thismat[1,2] = matrix['m12']
    thismat[1,3] = matrix['m13']
    thismat[2,0] = matrix['m20']
    thismat[2,1] = matrix['m21']
    thismat[2,2] = matrix['m22']
    thismat[2,3] = matrix['m23']
    thismat[3,0] = matrix['m30']
    thismat[3,1] = matrix['m31']
    thismat[3,2] = matrix['m32']
    thismat[3,3] = matrix['m33']
    
    M_list.append(thismat)
    
    M = np.dot(M.T,thismat)
    


# extract registration point positions


p_idx = list()
pts = list()

for child in root_em.iter():
    pt = np.zeros(2)
    if child.tag == 'position':
        
        for coords in child.getiterator():            
            if coords.tag == 'pos_x':
                pt[0] = float(coords.text)
            elif coords.tag == 'pos_y':
                pt[1] = float(coords.text)
            #elif coords.tag == 'pos_z':
            #    pt[2] = float(coords.text)
            
        pts.append(pt)
            
    elif child.tag == 'name':
        p_idx.append(int(child.text[child.text.rfind(' '):]))
                
    
### TODO ##


                
                

# create new file by copying the header of the input file
newnavf = navfile[:-4] + '_icy.nav'

em.write_navfile(newnavf,outitems,xml=False)
    

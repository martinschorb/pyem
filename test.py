# -*- coding: utf-8 -*-
"""
Created on Tue Apr  6 10:49:32 2021

@author: schorb
"""

import requests
import zipfile
import os
from subprocess import Popen,PIPE
# import hashlib

cwd = os.getcwd()


if not os.path.exists('pyem_tests'):    
    # download and prepare test data 
    
    print('downloading test data ...')
    
    url = 'https://oc.embl.de/index.php/s/NDAkNzEr7zjSZ3Q/download'
    
    myfile = requests.get(url)
    open('test.zip','wb').write(myfile.content)
    
    with zipfile.ZipFile('test.zip', 'r') as unzip:
        unzip.extractall()
        
    os.remove('test.zip')
    

if not os.path.exists('applications'):   
    # download test scripts

    os.mkdir('applications')
    
    url = 'https://git.embl.de/schorb/pyem/-/raw/master/applications/virt_anchormaps.py?inline=false'
    
    anchfile = requests.get(url)
    open('applications/virt_anchormaps.py','wb').write(anchfile.content)
    
    url = 'https://git.embl.de/schorb/pyem/-/raw/master/applications/maps_acquire_cmd.py?inline=false'
    
    reffile = requests.get(url)
    open('applications/maps_acquire_cmd.py','wb').write(reffile.content)


#start tests
    
print('Testing map extraction for Tecnai...')

cd(os.path.join(cwd,'pyem_tests'))
p = Popen('python "'+os.path.join(cwd,'applications','maps_acquire_cmd.py')+'" "'+ os.path.join(cwd,'tecnai.nav')+'"', shell=True,stderr=PIPE,stdout=PIPE)

# test_hashlist = []
# print('comparing file hashes')
# for file in ['tecnai_automaps.nav','virt_map_p1.mrc','virt_map_p2.mrc','virt_map_p3.mrc','virt_map_p4.mrc']:
#     test_hashlist.append(hashlib.md5(open(file,'rb').read()).hexdigest())


    
print('Testing map extraction for Krios...')

p = Popen('python "'+os.path.join(cwd,'applications','virt_anchormaps.py')+'" "'+ os.path.join(cwd,'cryo_test_edge.nav')+'"', shell=True,stderr=PIPE,stdout=PIPE)



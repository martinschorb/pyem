#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr 30 13:34:25 2021

@author: schorb
"""

import os

import numpy as np

import dask.array as da
from dask.array import image

from dask.distributed import Client

from skimage.io import imsave


def findbgtiles(i,im=[],irange=255,stddev_limit=0.1):
    std=(im[:,:,i].std()/irange)
    
    if std.compute() < stddev_limit:
        return im[:,:,i]
    else:
        return da.zeros(im.shape[0:2])



def bg_correct(im,client,stddev_limit=0.1):
    irange = im.max() - im.min()
    
    a=client.map(findbgtiles,range(im.shape[2]),im=im,irange=irange,stddev_limit=stddev_limit)
    
    res = client.gather(a)
    
    btiles=da.sum(da.stack(res),axis=0)
    
    if btiles.max().compute()==0:
        correction = da.ones(im.shape[0:2])
    else:
        correction = btiles/btiles.max()
        
    
    return (im/np.stack([correction]*im.shape[2],axis=2)).compute()
    



def correct_mergedmap(mm,outdir):   
    
    im_in = mm['im']
    
    if type(im_in) == list:
        outtype = 'tif'
        im = image.imread(os.path.commonprefix(im_in)+'*')
        im = im.swapaxes(0,2)
    else:
        outtype = 'mrc'
        im = da.from_array(im_in, chunks=(-1,-1,1))
        
    client = Client()
    
    corr_im = bg_correct(im,client) 
    
    if outtype == 'tif':
        outfiles=[os.path.join(outdir,infile.split(os.path.commonpath(mm['im']))[1].strip('/')) for infile in mm['im']]
        
        for idx,outfile in enumerate(outfiles):
            imsave(outfile, corr_im[:,:,idx])
        
        
        
        
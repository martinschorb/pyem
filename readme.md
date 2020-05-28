# py-EM

![py-EM](doc/images/py-EM.png "py-EM Logo")



### a Python package to interact with SerialEM to enable [automated Transmission Electron Microscopy](https://doi.org/10.1038/s41592-019-0396-9)

1. [Installation instructions](#installation)

2. [Get started](#tutorials)

3. [Community and Support](#community)

4. [Set up integration in SerialEM GUI](https://git.embl.de/schorb/pyem/blob/master/doc/serialemtools.md)

5. [Set up KNIME](https://git.embl.de/schorb/pyem/blob/master/doc/knime.md) 

6. [Function List](#Functions)



## Installation instructions<a name="installation"></a>

- Install Anaconda from [here](https://www.anaconda.com/download/ "Download Anaconda"). Py-EM has been tested to work with both Python 2 and 3. Choose the appropriate OS.
- Start the Anaconda [Navigator](http://docs.anaconda.com/anaconda/user-guide/getting-started/ "Getting started with Anaconda").
- as explained in [section 4](http://docs.anaconda.com/anaconda/user-guide/getting-started/#run-python-in-a-jupyter-notebook "Run Python in a Jupyter Notebook"), install and start a Jupyter notebook.
- Download this [tutorial file](https://git.embl.de/schorb/pyem/raw/master/pyEM.ipynb?inline=false) (use "save link as..." if it shows in the browser), open it in your Jupyter session and follow the instructions.

## Get started<a name="tutorials"></a>
In order to access the Tutorials on how to use py-EM, follow these steps:

- as explained in [section 4](http://docs.anaconda.com/anaconda/user-guide/getting-started/#run-python-in-a-jupyter-notebook "Run Python in a Jupyter Notebook"), install and start a Jupyter notebook.
- Download this [tutorial file](https://git.embl.de/schorb/pyem/raw/master/pyEM.ipynb?inline=false) (use "save link as..." if it shows in the browser), open it in your Jupyter session and follow the instructions.

## Community and Support<a name="community"></a>

In order to receive announcements about updates or major changes in py-EM, we have set up a mailing list. In order to join it, please send an email to pyem-subscribe@embl.de.

Specific questions about applications and tricks should be posted to the joint forum of related scientific open software projects at https://forum.image.sc/tags/py-em.

Please contact me if you like to contribute applications or other pieces of code to py-EM and you will get an account for this gitlab platform.


## Set up integration in SerialEM GUI

Find out how to make py-EM and other external tools available through SerialEM's GUI [here](https://git.embl.de/schorb/pyem/blob/master/doc/serialemtools.md)

## Set up KNIME

Find out how to link py-EM and other external tools using KNIME [here](https://git.embl.de/schorb/pyem/blob/master/doc/knime.md)



## Function list:<a name="Functions"></a>

generic functions to parse/manipulate navigator/adoc files

- **loadtext:**  reads a text file in a list of strings (line-by-line)
- **nav_item:**  extracts a single navigator item from a text list - input: label, text - output: dict, list of remaining items
- **mdoc_item:**  extracts a single item from a mdoc text list - input: label, text - output: dict
- **parse_adoc:**  converts an adoc format text list into a list of dictionaries
- **fullnav:**  parses a full nav file (text list) and returns a list of dictionaries
- **itemtonav:**  converts a dictionary autodoc item variable into text list suitable for export into navigator format
- **newID:**  checks if the provided item ID already exists in a navigator and gives the next unique ID - input:list of dict, integer ID
- **newreg:** gives the next available registration for the input set of navigator items 
- **duplicate_items:** duplicates items from a list, optional second parameter is a list of labels of the items to duplicate. Default is to use the _Acquire_ flag. Optionally dupicates associated maps as well.
- **nav_find:** finds navigator items with a given key/value pair.
- **nav_selection:**  extracts a selection of navigator items into a new navigator, _Acquire_ can be chosen as a default flag, - input: list of items = optional list of item labels
- **navlabel_match:** identifies navigator items whose labels contain the given string
- **ordernav:**  re-orders a navigator by its label. It considers the indexing after a delimiter in the string. Example: s01_cell-1,s02_cell-1,s01_cell-02, ... is sorted by cells instead of s. When no delimiter is given (''), the navigator is sorted by its label.
- **xmltonav:** parses a navigator file stored in XML-format - input: text list, ouput navigator dictionary
- **write_navfile:** writes a new Navigator file from a list of item dictionaries - input:filename(str),list of nav dicts

functions to extract information from a navigator item

- **map_file:**  extracts the file name of a map item. Looks for the image file in absolute and relative path.
- **map_header:**  extracts parts of an MRC header. input: memory-mapped mrc object (see _mrcfile_ package)
- **realign_map:**  determines which map to align to for given navigator item
- **get_pixel** determines the pixel coordinates of a navigator item in its associated map (either merged or on the tile) 

main functions that provide key actions

- **mergemap:**  processes a map item and merges the mosaic using IMOD tools, generates a dictionary with metadata for this procedure
- **img2polygon:**  converts a binary image into a polygon (list of points) describing its outline
- **map_extract:**  extracts an image from a given position in an existing map and links positions inside
- **pts2nav:**  takes pixel coordinates on an input map, generates virtual maps at their positions, creates polygons matching their shape
- **outline2mod:**  takes an input image of label outlines (single pixel thickness), creates an IMOD model file with these outlines as contours.


accessory functions;

- **map_matrix:**  determine the matrix relating pixel and stage coordinates of a map
- **cart2pol, pol2cart:** coordinate conversions
- **imcrop:**  crops an image of a given size (2 element numpy array) around a pixel coordinate (2 element numpy array)
- **findfile** will find files that match a search string in subfolders of the provided search directory
    
   

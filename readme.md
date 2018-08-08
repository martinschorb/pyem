# emTools

### a Python package to interact with SerialEM to enable automated Transmission Electron Microscopy

## Function list:

generic functions to parse/manipulate navigator/adoc files

- **loadtext:**  reads a text file in a list of strings (line-by-line)
- **nav_item:**  extracts a single navigator item from a text list - input: label, text - output: dict, list of remaining items
- **mdoc_item:**  extracts a single item from a mdoc text list - input: label, text - output: dict
- **parse_adoc:**  converts an adoc format text list into a list of dictionaries
- **fullnav:**  parses a full nav file (text list) and returns a list of dictionaries
- **itemtonav:**  converts a dictionary autodoc item variable into text list suitable for export into navigator format
- **newID:**  checks if the provided item ID already exists in a navigator and gives the next unique ID - input:list of dict, integer ID
- **newreg:** gives the next available registration for the input set of navigator items 
- **duplicate_items:** duplicates items from a list, optional second parameter is a list of labels of the items to duplicate. Default is to use the _Acquire_ flag. 
- **nav_selection:**  extracts a selection of navigator items into a new navigator, _Acquire_ can be chosen as a default flag, - input: lis tof items, optional list of item labels
- **ordernav:**  re-orders a navigator by its label. It considers the indexing after a delimiter in the string. Example: s01_cell-1,s02_cell-1,s01_cell-02, ... is sorted by cells instead of s. When no delimiter is given (''), the navigator is sorted by its label.

functions to extract information from a navigator item

- **map_file:**  extracts the file name of a map item. Looks for the image file in absolute and relative path.
- **map_header:**  extracts parts of an MRC header. input: memory-mapped mrc object (see _mrcfile_ package)
- **realign_map:**  determines which map to align to for given navigator item
- **get_mergepixel** determines the pixel coordinates of a navigator item in its associated map. 

main functions that provide key actions

- **mergemap:**  processes a map item and merges the mosaic using IMOD tools, generates a dictionary with metadata for this procedure
- **img2polygon:**  converts a binary image into a polygon (list of points) describing its outline
- **map_extract:**  extracts an image from a given position in an existing map and links positions inside
- **pts2nav:**  takes pixel coordinates on an input map, generates virtual maps at their positions, creates polygons matching their shape
- **outline2mod:**  takes an input image of label outlines (single pixel thickness), creates an IMOD model file with these outlines as contours.


accessory functions;

- **map_rotation:**  determine rotation of a map's coordinate frame
- **cart2pol, pol2cart:** coordinate conversions
- **imcrop:**  crops an image of a given size (2 element numpy array) around a pixel coordinate (2 element numpy array)
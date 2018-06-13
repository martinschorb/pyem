# EM tools

### a python package to interact with Serial EM to enable automated Transmission Electron Microscopy

## Function list:

generic functions to parse/manipulate navigator/adoc files

- **loadtext:**  reads a text file in a list of strings (line-by-line)
- **nav_item:**  extracts a single navigator item from a text list - input: label, text - output: dict
- **mdoc_item:**  extracts a single item from a mdoc text list - input: label, text - output: dict
- **parse_adoc:**  converts an adoc format text list into a list of dictionaries
- **fullnav:**  parses a full nav file (text list) and returns a list of dictionaries
- **itemtonav:**  converts a dictionary autodoc item variable into text list suitable for export into navigator format
- **newID:**  checks if the provided item ID already exists in a navigator and gives the next unique ID - input:list of dict, integer ID
- **nav_selection:**  extracts a selection of navigator items into a new navigator, _Acquire_ can be chosen as a default flag, - input: list, optional list of items


functions to extract information from a navigator item

- **map_file:**  extracts the file name of a map item. Looks for the image file in absolute and relative path.
- **map_header:**  extracts parts of an MRC header. input: memory-mapped mrc object (see _mrcfile_ package)
- **realign_map:**  determines which map to align to for given navigator item

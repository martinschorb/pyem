# EM tools

### a python package to interact with Serial EM to enable automated Transmission Electron Microscopy

## Function list:

generic functions to parse navigator/adoc files

- **loadtext:**  reads a text file in a list of strings (line-by-line)
- **nav_item:**  extracts a single navigator item from a text list - input: label, text - output: dict
- **mdoc_item:**  extracts a single item from a mdoc text list - input: label, text - output: dict
- **parse_adoc:**  converts an adoc format text list into a list of dictionaries

functions to extract information from a navigator item

- **map_file:**  extracts the file name of a map item. Looks for the image file in absolute and relative path.
- **map_header:**  extracts parts of an MRC header. input: memory-mapped mrc object (see _mrcfile_ package)
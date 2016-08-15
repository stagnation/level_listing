level_listing
=============

A simple script to generate a html page with the levelshots found inside quake3 .pk3 levelfiles


Usage
=====

usage: level_listing.py [-h] [-v] [--output-dir OUTPUT_DIR]
                        [--input-dir INPUT_DIR]
                        [--levelshot-extract-path LEVELSHOT_EXTRACT_PATH]
                        [--temp-dir TEMP_DIR]

Quake 3 map list html writer, parses a directory of pk3 files and generates a
html page with titles and levelshots

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         verbose output
  --output-dir OUTPUT_DIR
                        output directory
  --input-dir INPUT_DIR
                        input directory with pk3 files
  --levelshot-extract-path LEVELSHOT_EXTRACT_PATH
                        path where levelshots should be extracted
  --temp-dir TEMP_DIR   temporary directory to extract level data generate
                        automatically but can be overwritten with this flag

Directory Structure
===================
the program requires the following directory tree:

index-dir
	-images
		-favicon
			-favicon.ico
		-levels

*todo if there is no master .arena file, search for individual .arena files with the map longname


DEPENDENCIES:

* Wand, python bindings to imagemagick, and imagemagick in order to transform .tga levelshots to .png.
* zipfile
* tempfile (optional, temporary file path can be specified manually)
* shutil
* argparse



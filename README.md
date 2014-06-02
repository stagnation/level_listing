level_listing
=============

A simple script to generate a html page with the levelshots found inside quake3 .pk3 levelfiles


usage: put .pk3 files in images/quake/online or .jpg files in images/quake/request
and call generate_menu.py

arguements: 
1) index_directory, where you want the html file to be generated, the file listing will sprawl from here.
2) pk3_directory, the folder where the pk3 files are saved.
3) levelshot_override_directory, if any levelshots should be overriden place them here with the same filename.
4) true/flase for read from level_title_file. this file is generated if the program is run with 0 or f for the fourth argument and this will create a text file with all the levelcodes and longnames from the pk3 files. The longnames can then be edited in this file and next time the program is run these edited longnames will be used instead of the longnames found in the .pk3-file





the program requires the following directory tree:

index-dir
	-images
		-favicon
			-favicon.ico
		-levels
		-request
			-comments.txt

the request folder will be scanned for .jpg files with a levelshot for a requested map that is not currently in the main pk3_dir. any comments saved in comments.txt will be added to the requested map in the list as well as the map name (filename.jpg)



DEPENDENCIES:

the script requiers Wand, python bindings to imagemagick, and imagemagick in order to transform .tga levelshots to .png.
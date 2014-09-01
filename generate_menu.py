import zipfile
import glob
import sys
import os.path
import re
import tempfile
import shutil

from wand.image import Image
verbose = True

def convert_image(input_file_path, convert_format):

    output_file_path = input_file_path[:input_file_path.rfind('.')] + "." + convert_format
    if verbose: print output_file_path
    with Image(filename = input_file_path) as img:
        if verbose: print img.format
        with img.convert(convert_format) as conv:
            if verbose: print conv.format
            img.save(filename=output_file_path)
            return output_file_path

def is_image(file):
    if file.endswith("jpg"):
        return True
    elif file.endswith("JPG"):
        return True
    elif file.endswith("tga"):
        return True
    elif file.endswith("TGA"):
        return True      
    elif file.endswith("png"):
        return True
    elif file.endswith("PNG"):
        return True    

    else:
        return False 
        
def is_non_html_image(file):
    if file.endswith("tga"):
        return True
    elif file.endswith("TGA"):
        return True
       
    else:
        return False
    

class QuakeLevel:
    

    
    def init(self, pk3_filepath, levelshot_extract_path, temporary_file_storage):
        
        self.arena_file = ""
    
        self.filename = ""
        self.filename_full = ""
    

        self.mapcount = 0
    
        self.longname_list = []
    
        self.levelcode_list = []
        self.levelshot_int_list = []
        self.levelshot_ext_list = []
    
    
        self.is_mappack = False
        
        self.filename_full = os.path.basename(pk3_filepath)
        
        self.filename = self.filename_full[: self.filename.find('.') - 3] #minus 3 ???? 
        #removes fileformat from name
        
        convert_image_format = "png"
        
        #construct a list of all member inside the 'zip' file.
        if zipfile.is_zipfile(pk3_filepath):
            zipper = zipfile.ZipFile(pk3_filepath, 'r')
        else:
            raise zipfile.BadZipfile()   
            
        content = zipper.namelist()
        if "maplist.txt" in content:
            zipper.getinfo("maplist.txt")
            if verbose: print str(self.filename) + " is a mappack"
            if verbose: print ""
            self.is_mappack = True
        
        for cont in content:
            #find levelshot: is_image details acceptable image files
            if cont.startswith("levelshots") and is_image(cont):
                self.levelshot_int_list.append(cont)
  
            #find levelcode from the .bsp file    
            elif cont.endswith(".bsp"):
                self.levelcode_list.append(cont.replace("maps/", '').replace(".bsp", ''))
                self.mapcount += 1
                
            #fine .arena file with map metadata
            elif cont.endswith(".arena"):
                self.arena_file = cont
                

        #at this point all variables should be initilized, parsed from the pk3 file.        
        if self.arena_file == "":
            if verbose: print "warning no arena file found for"
            if verbose: print self.filename
            if verbose: print "longname/s copied from levelcode/s"
            if verbose: print ""
            self.longname_list = self.levelcode_list[:]
            
                    
                    
        for levelshot in self.levelshot_int_list:
            if levelshot != "":
                zipper.extract(levelshot, levelshot_extract_path)
                levelshot_file_path = os.path.join(levelshot_extract_path, levelshot)
                
                if is_non_html_image(levelshot_file_path):
                    levelshot_file_path = convert_image(levelshot_file_path, convert_image_format)
                    if verbose: print self.filename + " converted to " + convert_image_format
                    
                if verbose: print levelshot_file_path
                self.levelshot_ext_list.append(levelshot_file_path)
                    
        
        
        #extract the .arena file with meta data to a temporary storage to read data from it.
        arena_file_map_code_list = []
        if self.arena_file != "":
            zipper.extract(self.arena_file, temporary_file_storage)
            with open(os.path.join(temporary_file_storage, self.arena_file)) as f: 
                arena_data = f.readlines()
            for line in (arena_data):
                if "longname" in line:
                    longname = line[line.find('"'):]
                    longname = re.sub('[^0-9a-zA-Z ]+', '', longname)
                    self.longname_list.append(longname) #
                    
                if "map" in line: #alternative metho of getting the levelcode. which is better?
                    mapcode = line[line.find('"'):]
                    
                     
                     
                    mapcode = re.sub('[^0-9a-zA-Z]+', '', mapcode)
                    arena_file_map_code_list.append(mapcode)
                
                
        #rearrange longname list to be in the same order as the other lists by comparing
        #the given mapcode in the arena file to the levelcode list (which is ordered 
        #in the same fashion as levelist)    
        
           
        #levelcode list is sorted like 1 10 11 2 3 4 ...
        #arena_file_map_code_list is sorted like 1 2 3 4 ... 10 11
        
        
        longname_list_copy = self.longname_list[:]
        possible_mismatch = False
                    
        if self.arena_file != "":
            for i, mapcode in enumerate(self.levelcode_list):
                if i >= len(arena_file_map_code_list):
                    #if not all maps are listed in the arena file
                    #should still be able to work with the index lookup
                    if verbose: print "warning: not all maps are listed in the arena file of " + self.filename
                    possible_mismatch = True
                    #find the index in levelcode_list that corresponds to the given arena_file
                    if mapcode in arena_file_map_code_list:
                        k = arena_file_map_code_list.index(mapcode)
                        if i < len(self.longname_list):
                            self.longname_list[i] = longname_list_copy[k]
                        else:
                            self.longname_list.append(longname_list_copy[k])
                    else:
                        if verbose: print "warning: levelcodes from .bsp files in " + self.filename + " do not match longnames parsed from the .arena file."
                        
                elif self.levelcode_list[i] != arena_file_map_code_list[i]:
                    possible_mismatch = True
                    #find the index in levelcode_list that corresponds to the given arena_file
                    if mapcode in arena_file_map_code_list:
                        k = arena_file_map_code_list.index(mapcode)
                        if i < len(self.longname_list):
                            self.longname_list[i] = longname_list_copy[k]
                        else:
                            self.longname_list.append(longname_list_copy[k])    
                    else:
                        if verbose: print "warning: levelcodes from .bsp files in " + self.filename + " do not match longnames parsed from the .arena file."
                        

        if possible_mismatch:
            if verbose: print "warning possible order mismatch between map name and mapcode + levelshot for"
            if verbose: print self.filename        
            if verbose: print ""    
        
          
        if self.is_mappack:    
            if verbose: print "mappack " + self.filename + " contains " + str(self.mapcount) + " maps"
            #make sure that all lists are the same length or throw a warning
            if len(self.levelshot_int_list) != self.mapcount:
                if verbose: print "warning then number of internal levelshots do not match the number of levels"
            if len(self.levelshot_ext_list) != self.mapcount:
                if verbose: print "warning then number of external levelsohts do not match the number of levels"
            if len(self.longname_list) != self.mapcount: 
                if verbose: print "warning then number of longnames do not match the number of levels"
            if len(self.levelcode_list)!= self.mapcount:
                if verbose: print "warning then number of levelcodes do not match the number of levels"
            


            
        
    def check_if_override(self, levelshot_override_path):
        for i, levelshot in enumerate(self.levelshot_ext_list):
            if levelshot == "":
                if verbose: print "Error: no levelshot is extracted for " + filename
                if verbose: print "Run init for the file first" 
                return False
            
            
            else:
                override_file_path = os.path.join(levelshot_override_path, self.levelshot_int_list[i].replace("levelshots/", ''))
                if os.path.isfile(override_file_path):
                    if verbose: print "levelshot_overwritten for " + self.levelcode_list[i]
                    self.levelshot_ext_list[i] = override_file_path
                    return True
                    
                else:
                    return False    
                    
        
        
###############################

i = 1
index_dirr = sys.argv[i]
#index_dirr = "/Users/Spill/Documents/programering/quakeTML/git/level_listing/"
i += 1

pk3_dirr = sys.argv[i]
if verbose: print "found " + str(len(sys.argv)) + " input arguments"
if verbose: print ""
i += 1



#if the titles are not read from file all level titles will be saved to a file with their levelcodes.
#this file can then be overwritten to change the displayed longnames for a specific map
#by setting this argument to true and reading longname from the file rather than from the pk3

#make sure to run without reading the file before reading so all pk3 files are represented in the level 
#title file.


 

if len(sys.argv) > i:
    levelshot_override_path = sys.argv[i]
else:
    levelshot_override_path = os.path.join(index_dirr, "levelshots/")
if verbose: print "workind dir is: " + index_dirr    
i += 1
    
if len(sys.argv) > i:
    if sys.argv[i] in ["true", "t", "y", "1", "True", "read"]:
        if verbose: print "reading titles file"
        read_level_titles = True
    if sys.argv[i] in ["false", "f", "n", "0", "False", "write"]:
        if verbose: print "writing to titles file"
        read_level_titles = False
else:
    read_level_titles = False            
i += 1        


if verbose: print "---\n"


###############################
#initializations and paths
#open and read from static html files     

temporary_file_dir = tempfile.mkdtemp()   
        

fileformat = '.jpg'
reqest_level_dirr = os.path.join(index_dirr, "images/quake/request/")
html_header = os.path.join(index_dirr, "html_header.html")
html_footer = os.path.join(index_dirr, "html_footer.html")
html_level_body_path = os.path.join(index_dirr, "html_level_body.html")
html_level_body = open(html_level_body_path, 'r').read()
html_divider_title_path = os.path.join(index_dirr, "html_divider_title.html")
html_divider_title = open(html_divider_title_path, 'r').read()

levelshot_extract_path = os.path.join(index_dirr, "images/levels")


menu_html_file = os.path.join(index_dirr, "index.html")
level_title_file = os.path.join(index_dirr, "level_titles.txt")

comment_file = os.path.join(reqest_level_dirr, "comments.txt")
comment_obj = open(comment_file, "ra+")
level_comments = comment_obj.readlines()


menu_obj = open(menu_html_file, "w")
header_obj = open(html_header, "r")
footer_obj = open(html_footer, "r")
level_titles_obj = open(level_title_file, "r+")

if read_level_titles:
    read_title_lines = level_titles_obj.readlines()
    read_title_codes = read_title_lines[:]
    read_title_names = read_title_lines[:]
    
    for i, line in enumerate(read_title_lines):

        split_index = line.find("\t")
        read_title_codes[i] = line[:split_index]
        read_title_names[i] = line[split_index + 1:]
else:
    read_title_codes = []
    read_title_names = []    

        

header = header_obj.read()
footer = footer_obj.read()

num_brs = 21 #number of html line break tags needed between rows of floating "level containers"-divs 

####################
#LEVELS ON SERVER
#parse data from .pk3 file
####################


menu_obj.write(header)
interim_divider = html_divider_title.format(image = os.path.join(index_dirr, "images/online_icon.png"), title = "kartor att spela", line1 = "dessa finns och spelas med angivet kommand", line2 = "")
menu_obj.write(interim_divider)

#

pk3_list = glob.glob(pk3_dirr + '/' + '*.pk3')

num_pk3s = len(pk3_list)
if verbose: print "found " + str(num_pk3s) + " pk3 files"
if verbose: print "---\n"
level_list = []

#create a list of all levels from .pk3 files and init also extracts the levelshot
for pk3 in pk3_list:
    level = QuakeLevel()
    try:
        level.init(pk3, levelshot_extract_path, temporary_file_dir)
        level.check_if_override(levelshot_override_path)
    
        level_list.append(level)
    except zipfile.BadZipfile:
        if verbose: print pk3 + " is not a valid pk3 file, skipping"
    
#

interim_title = ""    
interim_body = ""



#for all levels
mapcount = 0
for (i, level) in enumerate(level_list):
    num_maps = level.mapcount
    for j in range(num_maps):
        levelcode = level.levelcode_list[j]
        
        if read_level_titles:

            if levelcode in read_title_codes:
                longname = read_title_names[read_title_codes.index(level.levelcode_list[j])]
            else:
                if verbose: print "ERROR: no longname found for " + level.filename + " in map titles file " + level_title_file + " make sure to run the script with the read titles file argument set to false or write."
                    
        else:
            if j < len(level.longname_list):
                longname = level.longname_list[j]    
            else:
                if verbose: print "warning no longname found in " + level.filename
                longname = levelcode
        
        if j < len(level.levelshot_ext_list):
            levelshot = level.levelshot_ext_list[j]
        else:
            if verbose: print "warning missing levelshot for " + level.filename
            levelshot = ""
             
        level.levelcode_list[j]
        
        if level.is_mappack:    
            map_title = longname + "</b> in " + level.filename + "<b>"
            interim_title = html_level_body.format(map = map_title, comment = "\callvote map " + levelcode, levelshot = levelshot)
            mapcount += 1
        else: 
            map_title = longname
            interim_title = html_level_body.format(map = map_title, comment = "\callvote map " + levelcode, levelshot = levelshot)
            mapcount += 1    
            
        menu_obj.write(interim_title)
        if not read_level_titles:
            level_titles_obj.write(levelcode + "\t" + longname + "\n")
            
        
        #every second map, i e the right map out of two
        #if (i + j) % 2 == 1: 
        if mapcount % 2 == 0:
            for k in range(num_brs):
                menu_obj.write("<br/>")
                
#write some extra spacing after the last map
for j in range(2*num_brs): 
    menu_obj.write("<br/>")



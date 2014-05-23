import zipfile
import glob
import sys
import os.path
import re

def is_image(file):
    if file.endswith("jpg"):
        return True
    elif file.endswith("png"):
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
        
        #construct a list of all member inside the 'zip' file.
        zipper = zipfile.ZipFile(pk3_filepath, 'r')
        content = zipper.namelist()
        
        try:
            zipper.getinfo("maplist.txt")
            print str(self.filename) + " is a mappack"
            print ""
            self.is_mappack = True
            
        except KeyError: #error from get info i e not a mappack, ignore
            print ""
        
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
                    
                    
        for levelshot in self.levelshot_int_list:
            if levelshot != "":
                zipper.extract(levelshot, levelshot_extract_path)
                self.levelshot_ext_list.append(levelshot_extract_path + levelshot)
                    
        
        
        #extract the .arena file with meta data to a temporary storage to read data from it.
        arena_file_map_code_list = []
        if self.arena_file != "":
            zipper.extract(self.arena_file, temporary_file_storage)
            with open(os.path.join(temporary_file_storage, self.arena_file)) as f: 
                arena_data = f.readlines()
            for line in (arena_data):
                if "longname" in line:
                    self.longname_list.append(line[11: -3]) #
                if "map" in line: #alternative metho of getting the levelcode. which is better?
                    mapcode = line[5:]
                    mapcode = re.sub('[^0-9a-zA-Z]+', '', mapcode)
                    arena_file_map_code_list.append(mapcode)
                
                
        #rearrange longname list to be in the same order as the other lists by comparing
        #the given mapcode in the arena file to the levelcode list (which is ordered 
        #in the same fashion as levelist)    
        
           
        #levelcode list is sorted like 1 10 11 2 3 4 ...
        #arena_file_map_code_list is sorted like 1 2 3 4 ... 10 11
        
        longname_list_copy = self.longname_list[:]
        possible_mismatch = False
        
        for i, mapcode in enumerate(self.levelcode_list):
            if self.levelcode_list[i] != arena_file_map_code_list[i]:
                possible_mismatch = True
                #find the index in levelcode_list that corresponds to the given arena_file
                
                
                k = arena_file_map_code_list.index(mapcode)
                self.longname_list[i] = longname_list_copy[k]

        if possible_mismatch:
            print "warning possible order mismatch between map name and mapcode + levelshot for"
            print self.filename        
            print ""    
        
          
        if self.is_mappack:    
            print "mappack " + self.filename + " contains " + str(self.mapcount) + " maps"
            #make sure that all lists are the same length or throw a warning
            if len(self.levelshot_int_list) != self.mapcount:
                print "warning then number of internal levelshots do not match the number of levels"
            if len(self.levelshot_ext_list) != self.mapcount:
                print "warning then number of external levelsohts do not match the number of levels"
            if len(self.longname_list) != self.mapcount: 
                print "warning then number of longnames do not match the number of levels"
            if len(self.levelcode_list)!= self.mapcount:
                print "warning then number of levelcodes do not match the number of levels"
            


            
        
    def check_if_override(self, levelshot_override_path):
        for i, levelshot in enumerate(self.levelshot_ext_list):
            if levelshot == "":
                print "Error: no levelshot is extracted for " + filename
                print "Run init for the file first" 
                return False
            
            
            else:
                override_file_path = os.path.join(levelshot_override_path, self.levelshot_int_list[i].replace("levelshots/", ''))
                if os.path.isfile(override_file_path):
                    print "levelshot_overwritten for " + self.levelcode_list[i]
                    self.levelshot_ext_list[i] = override_file_path
                    return True
                    
                else:
                    return False    
                    
        
        
###############################

index_dirr = sys.argv[1]
#index_dirr = "/Users/Spill/Documents/programering/quakeTML/git/level_listing/"

pk3_dirr = sys.argv[2]
print "found " + str(len(sys.argv)) + " input arguments"
print ""


#if the titles are not read from file all level titles will be saved to a file with their levelcodes.
#this file can then be overwritten to change the displayed longnames for a specific map
#by setting this argument to true and reading longname from the file rather than from the pk3

#make sure to run without reading the file before reading so all pk3 files are represented in the level 
#title file.

if len(sys.argv) > 5:
    if sys.argv[5] in ["true", "t", "y", "1", "True"]:
        print "reading titles file"
        read_level_titles = True
    if sys.argv[5] in ["false", "f", "n", "0", "False"]:
        print "writing to titles file"
        read_level_titles = False
else:
    read_level_titles = False            
    

if len(sys.argv) > 4:
    temporary_file_dir = sys.argv[4]
else:
    temporart_file_dir = index_dirr    

if len(sys.argv) > 3:
    levelshot_override_path = sys.argv[3]
else:
    levelshot_override_path = os.path.join(index_dirr, "levelshots/")
print "workind dir is: " + index_dirr    





###############################
#initializations and paths
#open and read from static html files        
        

fileformat = '.jpg'
reqest_level_dirr = os.path.join(index_dirr, "images/quake/request/")
html_header = os.path.join(index_dirr, "html_header.html")
html_footer = os.path.join(index_dirr, "html_footer.html")
html_level_body_path = os.path.join(index_dirr, "html_level_body.html")
html_level_body = open(html_level_body_path, 'r').read()
html_divider_title_path = os.path.join(index_dirr, "html_divider_title.html")
html_divider_title = open(html_divider_title_path, 'r').read()

levelshot_extract_path = os.path.join(index_dirr, "images/quake/online/")


menu_html_file = os.path.join(index_dirr, "index.html")
level_title_file = os.path.join(index_dirr, "level_titles.txt")

with open(os.path.join(reqest_level_dirr, "comments.txt")) as f: 
    level_comments = f.readlines()


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
interim_divider = html_divider_title.format(image = os.path.join(index_dirr, "images/online_icon.png"), title= "kartor att spela", line1 = "dessa finns och spelas med angivet kommand", line2 = "")
menu_obj.write(interim_divider)

#


pk3_levelshot_path = os.path.join(pk3_dirr, "levelshots/")

pk3_list = glob.glob(pk3_dirr + '/' + '*.pk3')

num_pk3s = len(pk3_list)
print "found " + str(num_pk3s) + " pk3 files"

level_list = []

#create a list of all levels from .pk3 files and init also extracts the levelshot
for pk3 in pk3_list:
    level = QuakeLevel()
    level.init(pk3, levelshot_extract_path, temporary_file_dir)
    level.check_if_override(levelshot_override_path)
    
    level_list.append(level)
    
#

interim_title = ""    
interim_body = ""



#for all levels
for (i, level) in enumerate(level_list):
    num_maps = level.mapcount
    for j in range(num_maps):
        if read_level_titles:
            longname = read_title_names[read_title_codes.index(level.levelcode_list[j])]
        else:
            longname = level.longname_list[j]    
        
        
        if level.is_mappack:    
            map_title = longname + "</b> in " + level.filename + "<b>"
            interim_title = html_level_body.format(map = map_title, comment = "\callvote map " + level.levelcode_list[j], levelshot =level.levelshot_ext_list[j])
        else: 
            map_title = longname
            interim_title = html_level_body.format(map = map_title, comment = "\callvote map " + level.levelcode_list[j], levelshot =level.levelshot_ext_list[j])    
            
        menu_obj.write(interim_title)
        if not read_level_titles:
            level_titles_obj.write(level.levelcode_list[j] + "\t" + level.longname_list[j] + "\n")
        #every second map, i e the right map out of two
        if (i + j) % 2 == 1: 
            for j in range(num_brs):
                menu_obj.write("<br/>")
                
#write some extra spacing after the last map
for j in range(num_brs): 
    menu_obj.write("<br/>")








####################
#REQUESTED LEVELS
#only levelshots .jpg
####################


interim_divider = html_divider_title.format(image = os.path.join(index_dirr, "images/offline_icon.png"), title= "kartor att skaffa", line1 = "dessa finns inte", line2 = "se individuella kommentarer")
menu_obj.write(interim_divider)


# generate a list of all levelshot images
levelshot_list = glob.glob(reqest_level_dirr + '*' + fileformat)
num_levels = len(levelshot_list) 
levelname_list = levelshot_list[:] #copt of levelshot list for size
for j in range(num_levels):
    levelname_list[j] = levelshot_list[j].replace(reqest_level_dirr, '').replace(fileformat, '')


interim_title = ""
interim_body = ""
#loop over the applicable levelshots and generate the body of the html file
for i in range(0, num_levels, 1):

    interim_title = html_level_body.format(map = levelname_list[i], comment = level_comments[i], levelshot = levelshot_list[i])
    menu_obj.write(interim_title)
        
    if i % 2 == 1 or i == num_levels - 1: #every second map, i e the right map out of two. and last
        for j in range(num_brs):
            menu_obj.write("<br/>")
    

        
menu_obj.write(footer)

menu_obj.close()
header_obj.close()
footer_obj.close()

print "done"
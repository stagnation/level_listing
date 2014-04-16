import zipfile
import glob
import sys
import os.path

def dirr_slash(str): #pass by reference?
    if str[len(str) - 1] != '/':
        str = str + '/'
    
    return str
    

class QuakeLevel:
    levelcode = ""
    filename = ""
    filename_full = ""
    levelshot_int = ""
    levelshot_ext = ""
    content = []
    
    def init(self, pk3_filepath, levelshot_extract_path):
        
        self.filename_full = os.path.basename(pk3_filepath)
        
        self.filename = self.filename_full[: self.filename.find('.') - 3] #minus 3 ???? 
        #removes fileformat from name
        zipper = zipfile.ZipFile(pk3_filepath, 'r')
        content = zipper.namelist()
        
        for k in range(len (content)):
            if content[k].startswith("levelshots") and content[k].endswith(".jpg"):
                self.levelshot_int = content[k]
            elif content[k].endswith(".bsp"):
                self.levelcode = content[k].replace("maps/", '').replace(".bsp", '')
                
        zipper.extract(self.levelshot_int, levelshot_extract_path)    
        self.levelshot_ext = levelshot_extract_path + self.levelshot_int
        
        
    def check_if_override(self, levelshot_override_path):
        
        if self.levelshot_ext == "":
            print "run init first"
            return False
        
        
        else:
            override_file_path = levelshot_override_path + self.levelshot_int.replace("levelshots/", '')
            if os.path.isfile(override_file_path):
                print "levelshot_overwritten for " + self.levelcode
                self.levelshot_ext = override_file_path
                return True
                
            else:
                return False    
                
        
        
###############################

index_dirr = dirr_slash(sys.argv[1])
#index_dirr = "/Users/Spill/Documents/programering/quakeTML/git/level_listing/"

pk3_dirr = dirr_slash(sys.argv[2])
print len(sys.argv)
if len(sys.argv) > 3:
    levelshot_override_path = dirr_slash(sys.argv[3])
else:
    levelshot_override_path = index_dirr + "levelshots/"
print "workind dir is: " + index_dirr    





###############################
#initializations and paths
#open and read from static html files        
        

fileformat = '.jpg'
reqest_level_dirr = index_dirr + "images/quake/request/"
html_header = index_dirr + "html_header.html"
html_footer = index_dirr + "html_footer.html"
html_body_dual = open(index_dirr + "html_body_dual.html", "r").read()
html_map_title_dual = open(index_dirr + "html_map_title_dual.html", "r").read()
html_body_single = open(index_dirr + "html_body_single.html", "r").read()
html_map_title_single = open(index_dirr + "html_map_title_single.html", "r").read()
html_division_title = open(index_dirr + "html_division_title.html", "r").read()

levelshot_extract_path = index_dirr +"images/quake/online/"


menu_html_file = index_dirr + "menu.html"

with open(reqest_level_dirr + "comments.txt") as f: 
    level_comments = f.readlines()


menu_obj = open(menu_html_file, "w")
header_obj = open(html_header, "r")
footer_obj = open(html_footer, "r")

header = header_obj.read()
footer = footer_obj.read()

####################
#LEVELS ON SERVER
#parse data from .pk3 file
####################


menu_obj.write(header)
interim_division = html_division_title.format(image = index_dirr + "images/online_icon.png", title= "kartor att spela", line1 = "dessa finns och spelas med angivet kommand", line2 = "")
menu_obj.write(interim_division)

#


pk3_levelshot_path = pk3_dirr + "levelshots/"
pk3_file_list = glob.glob(pk3_dirr + '*.pk3')

num_pk3s = len(pk3_file_list)

level_list = []

#create a list of all levels from .pk3 files and init also extracts the levelshot
for j in range(num_pk3s):
    level = QuakeLevel()
    level.init(pk3_file_list[j], levelshot_extract_path)
    level.check_if_override(levelshot_override_path)
    
    level_list.append(level)
    
#

interim_title = ""    
interim_body = ""


for i in range (0, num_pk3s, 2): #for all levels
    j = i + 1 
    if not (i == num_pk3s - 1): #unless last (odd level) - process levels in pairs

        interim_title = html_map_title_dual.format(map1=level_list[i].filename, map2=level_list[j].filename, comment1="\callvote map "+level_list[i].levelcode, comment2="\callvote map " + level_list[j].levelcode)
        print
        interim_body = html_body_dual.format(path1=level_list[i].levelshot_ext, path2=level_list[j].levelshot_ext)
        
        menu_obj.write(interim_title)
        menu_obj.write(interim_body)
        
    else: #last single level - process individually
        
        interim_title = html_map_title_single.format(map1=level_list[i].filename, comment1="\callvote map "+ level_list[i].levelcode)
        
        interim_body = html_body_single.format(path1=level_list[i].levelshot_ext)
        
        menu_obj.write(interim_title)
        menu_obj.write(interim_body)


####################
#REQUESTED LEVELS
#only levelshots .jpg
####################


interim_division = html_division_title.format(image = index_dirr + "images/offline_icon.png", title= "kartor att skaffa", line1 = "dessa finns inte", line2 = "se individuella kommentarer")
menu_obj.write(interim_division)


# generate a list of all levelshot images
levelshot_list = glob.glob(reqest_level_dirr + '*' + fileformat)
num_levels = len(levelshot_list) 
levelname_list = levelshot_list[:] #copt of levelshot list for size
for j in range(num_levels):
    levelname_list[j] = levelshot_list[j].replace(reqest_level_dirr, '').replace(fileformat, '')


interim_title = ""
interim_body = ""
#loop over the applicable levelshots and generate the body of the html file
for i in range(0, num_levels, 2):
    j = i + 1
    if not (i == num_levels - 1):
        interim_title = html_map_title_dual.format(map1=levelname_list[i], map2=levelname_list[j], comment1= level_comments[i], comment2 = level_comments[j])
        
        menu_obj.write(interim_title)
        
        interim_body = html_body_dual.format(path1 = levelshot_list[i], path2 = levelshot_list[j])
        menu_obj.write(interim_body)
    else:
        interim_title = html_map_title_single.format(map1 = levelname_list[i], comment1 = level_comments[i])
        menu_obj.write(interim_title)
        interim_body = html_body_single.format(path1 = levelshot_list[i])
        menu_obj.write(interim_body)
    

        
menu_obj.write(footer)

menu_obj.close()
header_obj.close()
footer_obj.close()

print "done"
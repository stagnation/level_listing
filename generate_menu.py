import zipfile
import glob
import sys
import os.path


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
        
        for cont in content:
            if cont.startswith("levelshots") and cont.endswith(".jpg"):
                self.levelshot_int = cont
            elif cont.endswith(".bsp"):
                self.levelcode = cont.replace("maps/", '').replace(".bsp", '')
                
        zipper.extract(self.levelshot_int, levelshot_extract_path)    
        self.levelshot_ext = levelshot_extract_path + self.levelshot_int
        
        
    def check_if_override(self, levelshot_override_path):
        
        if self.levelshot_ext == "":
            print "run init first"
            return False
        
        
        else:
            override_file_path = os.path.join(levelshot_override_path, self.levelshot_int.replace("levelshots/", ''))
            if os.path.isfile(override_file_path):
                print "levelshot_overwritten for " + self.levelcode
                self.levelshot_ext = override_file_path
                return True
                
            else:
                return False    
                
        
        
###############################

index_dirr = sys.argv[1]
#index_dirr = "/Users/Spill/Documents/programering/quakeTML/git/level_listing/"

pk3_dirr = sys.argv[2]
print len(sys.argv)
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


menu_html_file = os.path.join(index_dirr, "menu.html")

with open(reqest_level_dirr + "comments.txt") as f: 
    level_comments = f.readlines()


menu_obj = open(menu_html_file, "w")
header_obj = open(html_header, "r")
footer_obj = open(html_footer, "r")

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

print pk3_dirr
pk3_list = glob.glob(pk3_dirr + '/' + '*.pk3')

num_pk3s = len(pk3_list)

level_list = []

#create a list of all levels from .pk3 files and init also extracts the levelshot
for j in range(num_pk3s):
    level = QuakeLevel()
    level.init(pk3_list[j], levelshot_extract_path)
    level.check_if_override(levelshot_override_path)
    
    level_list.append(level)
    
#

interim_title = ""    
interim_body = ""



#for all levels
for (i, level) in enumerate(level_list):
        
    interim_title = html_level_body.format(map = level.filename, comment = "\callvote map " + level.levelcode, levelshot =level.levelshot_ext)
        
    menu_obj.write(interim_title)
    if i % 2 == 1 or i == num_pk3s - 1: #every second map, i e the right map out of two. and last
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
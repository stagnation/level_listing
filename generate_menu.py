import zipfile
import glob
import sys
import os.path
import re
import tempfile
import shutil

from wand.image import Image
verbose = False


def convert_image(input_file_path, convert_format):

    output_file_path = input_file_path[:input_file_path.rfind('.')] + "." + convert_format
    #if verbose: print output_file_path
    with Image(filename = input_file_path) as img:
        #if verbose: print img.format
        with img.convert(convert_format) as conv:
            #if verbose: print conv.format
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

def get_code_from_shot(levelshot):
    return levelshot.replace("levelshots/", '').replace(".tga", '').replace(".png", '').replace(".JPG", '').replace(".jpg", '').replace("arenashots/", '')


def is_non_html_image(file):
    if file.endswith("tga"):
        return True
    elif file.endswith("TGA"):
        return True

    else:
        return False


class QuakeLevel:

    def init(self, pk3_filepath, settings, temporary_file_storage):

        self.arena_file = ""

        self.filename = ""
        self.filename_full = ""


        self.mapcount = 0

        self.longname_list = []

        self.levelcode_list = []
        self.levelshot_int_list = []
        self.levelshot_ext_list = []
        self.arenashot_list = []


        self.is_mappack = False
        self.is_multiarena = False

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
            self.is_mappack = True
        elif "maps.txt" in content:
            zipper.getinfo("maps.txt")
            self.is_mappack = True


        if verbose and self.is_mappack: print str(self.filename) + " is a mappack"
        if verbose and self.is_mappack: print "mappack " + self.filename + " contains " + str(self.mapcount) + " maps\n"


        for cont in content:
            #find levelshot: is_image details acceptable image files
            if cont.startswith("levelshots") and is_image(cont):
                self.levelshot_int_list.append(cont)

            #find levelcode from the .bsp file
            elif cont.endswith(".bsp"):
                self.levelcode_list.append(cont.replace("maps/", '').replace(".bsp", ''))
                self.mapcount += 1

            #find .arena file with map metadata
            elif cont.endswith(".arena"):
                self.arena_file = cont
            elif cont.endswith("arenas.txt"):
                self.arena_file = cont

            elif cont.startswith("arenashots") and is_image(cont):
                self.arenashot_list.append(cont)
                self.is_multiarena = True
                self.is_mappack = True



        #if there are several levelcodes in the map it's probably a mappack
        if len(self.levelcode_list) >= 2: self.is_mappack = True

        #at this point all variables should be initilized, parsed from the pk3 file.
        if self.arena_file == "":
            if verbose: print "warning no arena file found for " + self.filename
            if verbose: print "longname/s copied from levelcode/s\n"

            self.longname_list = self.levelcode_list[:]


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



                    mapcode = re.sub('[^0-9a-zA-Z]+', '', mapcode)#need to remove needless characters.
                    arena_file_map_code_list.append(mapcode)


        #new algorithm to get the correct longname for a levelcode in a mappack

        if self.is_mappack:
            if len(self.levelcode_list) > len(self.longname_list):
               for i in range(len(self.levelcode_list) - len(self.longname_list)):
                   self.longname_list.append("")


            longname_list_copy = self.longname_list[:]
            for i, levelcode in enumerate(self.levelcode_list):
                for k in range(len(arena_file_map_code_list)):
                    level_c = re.sub('[^0-9a-zA-Z]+', '', levelcode.lower()) #strip chars and lower
                    a_level_c = re.sub('[^0-9a-zA-Z]+', '', arena_file_map_code_list[k].lower()) #strip chars and lower
                    if level_c == a_level_c:
                        self.longname_list[i] = longname_list_copy[k]

        """
        apparently the name data was in arena file - scrapping this

        #attempt to read mapname data from maplist.txt or maps.txt
        #this


        #attempt to read mapname data from individual map .bsp
        #only do this if there is no chnace to grab longnames
        #from arena file - i e there is no .arena file

        if self.is_mappack and self.arena_file == "":
            print "attempting to read longnames from .bsp files"
            for level_code in levelcode_list:
                levelbsp = append(cont.replace("maps/", '').replace(".bsp", ''))
                levelbsp_file =  zipper.extract(levelbsp, temporary_file_storage)
                open(levelbsp_file, 'r')
        """

        #if the file is a multiarena, extract all the arenashots
        #first extracted levelshot is the parent levelshot for the arena map
        #the follwoing images are arenashots
        if self.is_multiarena:
            for arenashot in self.arenashot_list:
                arenacode = get_code_from_shot(arenashot)
                self.longname_list.append(arenacode)
                self.levelcode_list.append(arenacode)
                self.levelshot_int_list.append(arenashot)
                self.mapcount += 1

        #extract levelshots and save the extracted file paths in list levelshot_ext_list
        for levelshot in self.levelshot_int_list:
            if levelshot != "":
                zipper.extract(levelshot, settings['levelshot_extract_path'])
                levelshot_file_path = os.path.join(settings['levelshot_extract_path'], levelshot)

                if is_non_html_image(levelshot_file_path):
                    levelshot_file_path = convert_image(levelshot_file_path, convert_image_format)

                #here append
                self.levelshot_ext_list.append(levelshot_file_path)

        #if need be reorder levelshot_ext_list to correspond to levelshot_list's order
        levelshot_list_copy = self.levelshot_ext_list[:]

        if len(self.levelcode_list) > len(self.levelshot_ext_list):
            for i in range(len(self.levelcode_list) - len(self.levelshot_ext_list)):
                self.levelshot_ext_list.append("")

        for i, levelshot in enumerate(self.levelshot_int_list):
            levelshot_code = get_code_from_shot(levelshot)
            for k in range(len(self.levelcode_list)):
                levelshot_c = re.sub('[^0-9a-zA-Z]+', '', levelshot_code.lower()) #strip chars and lower
                self_levelc = re.sub('[^0-9a-zA-Z]+', '', self.levelcode_list[k].lower())
                if levelshot_c == self_levelc:
                    self.levelshot_ext_list[k] = levelshot_list_copy[i]

        if self.is_mappack:
            #make sure that all lists are the same length or throw a warning
            if len(self.levelshot_int_list) != self.mapcount:
                if verbose: print "warning then number of internal levelshots do not match the number of levels"
            if len(self.levelshot_ext_list) != self.mapcount:
                if verbose: print "warning then number of external levelsohts do not match the number of levels"
            if len(self.longname_list) != self.mapcount:
                if verbose: print "warning then number of longnames do not match the number of levels"
            if len(self.levelcode_list)!= self.mapcount:
                if verbose: print "warning then number of levelcodes do not match the number of levels"

            print ""

        if len(self.longname_list) <= len(self.levelcode_list):
            for i in range(len(self.longname_list)):
                if self.longname_list[i] == "":
                    self.longname_list[i] = self.levelcode_list[i]


    def check_if_override(self, override_path):
        for i, levelshot in enumerate(self.levelshot_ext_list):
            if levelshot == "":
                if verbose: print "Error: no levelshot is extracted for " + filename
                if verbose: print "Run init for the file first"
                return False


            else:
                override_file_path = os.path.join(override_path, self.levelshot_int_list[i].replace("levelshots/", ''))
                if os.path.isfile(override_file_path):
                    if verbose: print "levelshot_overwritten for " + self.levelcode_list[i]
                    self.levelshot_ext_list[i] = override_file_path
                    return True

                else:
                    return False



###############################

def parse_input_args(arguments):
    i = 1
    index_dirr = arguments[i]
    i += 1

    pk3_dirr = arguments[i]
    if verbose:
        print "found " + str(len(arguments)) + " input arguments\n"

        i += 1

    #if the titles are not read from file all level titles will be saved to a file with their levelcodes.
    #this file can then be overwritten to change the displayed longnames for a specific map
    #by setting this argument to true and reading longname from the file rather than from the pk3

    #make sure to run without reading the file before reading so all pk3 files are represented in the level
    #title file.

        levelshot_override_path = arguments[i]
    else:
        levelshot_override_path = os.path.join(index_dirr, "levelshots/")
    i += 1

    read_level_titles = False
    if len(arguments) > i:
        if arguments[i] in ["true", "t", "y", "1", "True", "read"]:
            if verbose: print "reading titles file"
            read_level_titles = True
        if arguments[i] in ["false", "f", "n", "0", "False", "write"]:
            if verbose: print "writing to titles file"
            read_level_titles = False
    else:
        read_level_titles = False
    i += 1

    if verbose: print "---\n"

    levelshot_extract_path = os.path.join(index_dirr, "images/levels")

    settings = {}
    settings['index_dirr'] = index_dirr
    settings['pk3_dirr'] = pk3_dirr
    settings['levelshot_override_path'] = levelshot_override_path
    settings['read_level_titles'] = read_level_titles
    settings['levelshot_extract_path'] = levelshot_extract_path
    return settings


def old_initialize_html_document(settings):
    # NB(nils): use argparse library for this
    fileformat = '.jpg'

    reqest_level_dirr = os.path.join(settings['index_dirr'], "images/quake/request/")
    html_header_path = os.path.join(settings['index_dirr'], "html_header.html")



    output_file = os.path.join(settings['index_dirr'], "index.html")
    level_title_file = os.path.join(settings['index_dirr'], "level_titles.txt")
    level_titles_obj = open(level_title_file, "r+")

    output_obj = open(output_file, "w")
    header_obj = open(html_header_path, "r")

    if settings['read_level_titles']:
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

    return res


class html_object:
    pass


def initialize_output_document(settings):
    html_header_path = os.path.join(settings['index_dirr'], "html_header.html")
    header_obj = open(html_header_path, "r")
    header = header_obj.read()

    output_obj = html_object()
    output_obj.path = os.path.join(settings['index_dirr'], "index.html")

    output_obj.text = open(output_obj.path, "w")

    output_obj.text.write(header)

    html_divider_title_path = os.path.join(settings['index_dirr'], "html_divider_title.html")
    html_divider_title = open(html_divider_title_path, 'r').read()
    interim_divider = html_divider_title.format(
            image = os.path.join(settings['index_dirr'], "images/online_icon.png"),
            title = "kartor att spela", line1 = "dessa finns och spelas med angivet kommand", line2 = "")

    output_obj.text.write(interim_divider) # NB(nils): byt detta namn
    return output_obj


def write_maps_to_output(output_obj, settings):
    num_brs = 21 #number of html line break tags needed between rows of floating "level containers"-divs
    pk3_list = glob.glob(settings['pk3_dirr'] + '/' + '*.pk3')

    html_level_body_path = os.path.join(settings['index_dirr'], "html_level_body.html")
    html_level_body = open(html_level_body_path, 'r').read()
    num_pk3s = len(pk3_list)

    output_file = os.path.join(settings['index_dirr'], "index.html")
    level_title_file = os.path.join(settings['index_dirr'], "level_titles.txt")
    level_titles_obj = open(level_title_file, "r+")

    if verbose: print "found " + str(num_pk3s) + " pk3 files \n --- \n"
    level_list = []

    #create a list of all levels from .pk3 files and init also extracts the levelshot
    for pk3 in pk3_list:
        level = QuakeLevel()
        try:
            level.init(pk3, settings, temporary_file_dir)
            level.check_if_override(settings['levelshot_override_path'])

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

            if settings['read_level_titles']:

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

            output_obj.text.write(interim_title)
            if not settings['read_level_titles']:
                level_titles_obj.write(levelcode + "\t" + longname + "\n")


            #every second map, i e the right map out of two
            #if (i + j) % 2 == 1:
            if mapcount % 2 == 0:
                for k in range(num_brs):
                    output_obj.text.write("<br/>")

    return output_obj


def write_output_footer(output_obj, settings):
    #write some extra spacing after the last map
    num_brs = 21 #number of html line break tags needed between rows of floating "level containers"-divs
    for j in range(2*num_brs):
        output_obj.text.write("<br/>")

    html_footer_path = os.path.join(settings['index_dirr'], "html_footer.html")
    footer_obj = open(html_footer_path, "r")
    footer = footer_obj.read()
    output_obj.text.write(footer)
    return output_obj


if __name__ == '__main__':
    print(sys.argv)
    settings = parse_input_args(sys.argv)
    temporary_file_dir = tempfile.mkdtemp()

    output_obj = initialize_output_document(settings)

    output_obj = write_maps_to_output(output_obj, settings)

    output_obj = write_output_footer(output_obj, settings)




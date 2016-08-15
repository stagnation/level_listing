import zipfile
import glob
import sys
import os.path
import re
import tempfile
import shutil

from wand.image import Image
verbose = False

# TODO(nils): overhaul all verbose printing
# TODO(nils): overhaul QuakeLevel class

class html_object:
    pass


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
    image_formats = ["jpg", "JPG", "tga", "TGA","png","PNG"]
    ext = file.split(".")[-1]
    if ext in image_formats:
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

        zippath = pk3_filepath
        #construct a list of all member inside the 'zip' file.
        if zipfile.is_zipfile(zippath):
            zipper = zipfile.ZipFile(zippath, 'r')
        else:
            raise zipfile.BadZipfile()

        zip_content = zipper.namelist()
        if "maplist.txt" in zip_content:
            zipper.getinfo("maplist.txt")
            self.is_mappack = True
        elif "maps.txt" in zip_content:
            zipper.getinfo("maps.txt")
            self.is_mappack = True

        # if verbose and self.is_mappack:
        #     print str(self.filename) + " is a mappack"
        # if verbose and self.is_mappack:
        #     print "mappack " + self.filename + " contains " + str(self.mapcount) + " maps\n"

        for cont in zip_content:
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
    settings['read_level_titles'] = read_level_titles
    settings['levelshot_extract_path'] = levelshot_extract_path
    return settings


# def old_initialize_html_document(settings):
#     # NB(nils): use argparse library for this
#     fileformat = '.jpg'

#     reqest_level_dirr = os.path.join(settings['index_dirr'], "images/quake/request/")
#     html_header_path = os.path.join(settings['index_dirr'], "html_header.html")

#     level_title_file = os.path.join(settings['index_dirr'], "level_titles.txt")
#     level_titles_obj = open(level_title_file, "r+")

#     output_obj = open(output_file, "w")
#     header_obj = open(html_header_path, "r")

#     if settings['read_level_titles']:
#         read_title_lines = level_titles_obj.readlines()
#         read_title_codes = read_title_lines[:]
#         read_title_names = read_title_lines[:]

#         for i, line in enumerate(read_title_lines):

#             split_index = line.find("\t")
#             read_title_codes[i] = line[:split_index]
#             read_title_names[i] = line[split_index + 1:]
#     else:
#         read_title_codes = []
#         read_title_names = []

#     header = header_obj.read()

#     return res


def initialize_output_document(settings, snippets):
    html_header_path = os.path.join(settings['index_dirr'], "html_header.html")
    header_obj = open(html_header_path, "r")
    header = header_obj.read()

    output_obj = html_object()
    output_obj.path = os.path.join(settings['index_dirr'], "index.html")

    output_obj.text = open(output_obj.path, "w")

    output_obj.text.write(header)

    divider = snippets['divider_title'].format(
            image = os.path.join(settings['index_dirr'], "images/online_icon.png"),
            title = "kartor att spela", line1 = "dessa finns och spelas med angivet kommand", line2 = "")

    output_obj.text.write(divider)
    return output_obj


def create_level_list(pk3_list, settings):
    #create a list of all levels from .pk3 files and init also extracts the levelshot
    level_list = []

    for pk3 in pk3_list:
        level = QuakeLevel()
        try:
            level.init(pk3, settings, temporary_file_dir)

            level_list.append(level)
        except zipfile.BadZipfile:
            if verbose: print pk3 + " is not a valid pk3 file, skipping"

    return level_list


def generate_map_obj_from_level_list(level_list):
    map_list = []
    for level in level_list:
        num_maps = level.mapcount

        for j in range(num_maps):
            map_obj = html_object()
            map_obj.levelcode = level.levelcode_list[j]

            if j < len(level.longname_list):
                map_obj.longname = level.longname_list[j]
            else:
                if verbose: print "warning no longname found in " + level.filename
                map_obj.longname = map_obj.levelcode

            if j < len(level.levelshot_ext_list):
                map_obj.levelshot = level.levelshot_ext_list[j]
            else:
                if verbose: print "warning missing levelshot for " + level.filename
                map_obj.levelshot = ""

            if level.is_mappack:
                map_obj.title = map_obj.longname + "</b> in " + level.filename + "<b>"
            else:
                map_obj.title = map_obj.longname

            map_list.append(map_obj)

    return map_list


def write_maps_to_output(output_obj, settings, snippets):
    num_brs = 21 #number of html line break tags needed between rows of floating "level containers"-divs
    pk3_list = glob.glob(settings['pk3_dirr'] + '/' + '*.pk3')

    if verbose: print "found " + str(num_pk3s) + " pk3 files \n --- \n"

    level_list = create_level_list(pk3_list, settings)

    # level_title_file = os.path.join(settings['index_dirr'], "level_titles.txt")
    # level_titles_obj = open(level_title_file, "r+")

    map_list = generate_map_obj_from_level_list(level_list)
    num_pk3s = len(pk3_list)

    # NB(nils): if longnames are to be overwritten do it here
    # NB(nils): if levelshots are to be overwritten do it here

    for (map_index, map_obj) in enumerate(map_list):
            
            interim_title = snippets['level_body'].format(
                    map = map_obj.title,
                    comment = "\callvote map " + map_obj.levelcode,
                    levelshot = map_obj.levelshot)
            
            output_obj.text.write(interim_title)
            # if not settings['read_level_titles']:
            #     level_titles_obj.write(
            #             map_obj.levelcode + "\t" + map_obj.longname + "\n")

            #every second map, i e the right map out of two
            if map_index % 2 != 0:
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


def construct_html_snippets():
    snippets = {}

    html_divider_title_path = os.path.join(settings['index_dirr'], "html_divider_title.html")
    html_divider_title = open(html_divider_title_path, 'r').read()
    snippets['divider_title'] = html_divider_title

    html_level_body_path = os.path.join(settings['index_dirr'], "html_level_body.html")
    html_level_body = open(html_level_body_path, 'r').read()
    snippets['level_body'] = html_level_body

    return snippets


if __name__ == '__main__':
    print(sys.argv)

    settings = parse_input_args(sys.argv)
    snippets = construct_html_snippets()

    temporary_file_dir = tempfile.mkdtemp()

    output_obj = initialize_output_document(settings, snippets)

    output_obj = write_maps_to_output(output_obj, settings, snippets)

    output_obj = write_output_footer(output_obj, settings)

    # all open files are closed as the program terminates

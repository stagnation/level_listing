#!/usr/bin/env python3

import argparse
import glob
import os.path
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

from wand.image import Image

# TODO(nils): overhaul all verbose printing
# TODO(nils): overhaul QuakeLevel class


class dummy_class:
    pass


def convert_image(input_file_path, convert_format):
    output_file_path = (
        input_file_path[: input_file_path.rfind(".")] + "." + convert_format
    )
    # if settings['verbose']: print(output_file_path)
    with Image(filename=input_file_path) as img:
        # if settings['verbose']: print(img.format)
        with img.convert(convert_format) as conv:
            # if settings['verbose']: print(conv.format)
            img.save(filename=output_file_path)
            return output_file_path


def is_image(file):
    image_formats = ["jpg", "JPG", "tga", "TGA", "png", "PNG"]
    ext = file.split(".")[-1]
    if ext in image_formats:
        return True
    else:
        return False


def get_code_from_shot(levelshot):
    return (
        levelshot.replace("levelshots/", "")
        .replace(".tga", "")
        .replace(".png", "")
        .replace(".JPG", "")
        .replace(".jpg", "")
        .replace("arenashots/", "")
    )


def is_non_html_image(file):
    if file.endswith("tga"):
        return True
    elif file.endswith("TGA"):
        return True
    else:
        return False


class QuakeLevel:
    def init(
        self,
        pk3_filepath,
        *,
        verbose: bool,
        levelshot_extract_path: Path,
        temporary_file_storage,
    ):
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

        self.filename = self.filename_full[
            : self.filename.find(".") - 3
        ]  # minus 3 ????
        # removes fileformat from name

        convert_image_format = "png"

        zippath = pk3_filepath
        # construct a list of all member inside the 'zip' file.
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

        for cont in zip_content:
            # find levelshot: is_image details acceptable image files
            if cont.startswith("levelshots") and is_image(cont):
                self.levelshot_int_list.append(cont)

            # find levelcode from the .bsp file
            elif cont.endswith(".bsp"):
                self.levelcode_list.append(cont.replace("maps/", '').replace(".bsp", ''))
                self.mapcount += 1

            # find .arena file with map metadata
            elif cont.endswith(".arena"):
                self.arena_file = cont
            elif cont.endswith("arenas.txt"):
                self.arena_file = cont

            elif cont.startswith("arenashots") and is_image(cont):
                self.arenashot_list.append(cont)
                self.is_multiarena = True
                self.is_mappack = True

        # if there are several levelcodes in the map it's probably a mappack
        if len(self.levelcode_list) >= 2:
            self.is_mappack = True

        if verbose and self.is_mappack:
            print(self.filename, "is a mappack and contains ", str(self.mapcount), " maps")

        # at this point all variables should be initialized, parsed from the pk3 file.
        if self.arena_file == "":
            if verbose:
                print("warning no arena file found for " + self.filename)
            if verbose:
                print("longname/s copied from levelcode/s\n")

            self.longname_list = self.levelcode_list[:]

        # extract the .arena file with meta data to a temporary storage to read data from it.
        arena_file_map_code_list = []
        if self.arena_file != "":
            zipper.extract(self.arena_file, temporary_file_storage)
            with open(os.path.join(temporary_file_storage, self.arena_file)) as f:
                arena_data = f.readlines()
            for line in (arena_data):
                if "longname" in line:
                    longname = line[line.find('"'):]
                    longname = re.sub('[^0-9a-zA-Z ]+', '', longname)
                    self.longname_list.append(longname)

                if (
                    "map" in line
                ):  # alternative method of getting the levelcode. which is better?
                    mapcode = line[line.find('"'):]

                    mapcode = re.sub('[^0-9a-zA-Z]+', '', mapcode)  # need to remove needless characters.
                    arena_file_map_code_list.append(mapcode)

        # new algorithm to get the correct longname for a levelcode in a mappack

        if self.is_mappack:
            if len(self.levelcode_list) > len(self.longname_list):
                for i in range(len(self.levelcode_list) - len(self.longname_list)):
                    self.longname_list.append("")

            longname_list_copy = self.longname_list[:]
            for i, levelcode in enumerate(self.levelcode_list):
                for k in range(len(arena_file_map_code_list)):
                    # strip chars and lower
                    level_c = re.sub('[^0-9a-zA-Z]+', '', levelcode.lower())
                    # strip chars and lower
                    a_level_c = re.sub('[^0-9a-zA-Z]+', '', arena_file_map_code_list[k].lower())
                    if level_c == a_level_c:
                        self.longname_list[i] = longname_list_copy[k]

        # if the file is a multiarena, extract all the arenashots
        # first extracted levelshot is the parent levelshot for the arena map
        # the following images are arenashots
        if self.is_multiarena:
            for arenashot in self.arenashot_list:
                arenacode = get_code_from_shot(arenashot)
                self.longname_list.append(arenacode)
                self.levelcode_list.append(arenacode)
                self.levelshot_int_list.append(arenashot)
                self.mapcount += 1

        # extract levelshots and save the extracted file paths in list levelshot_ext_list
        for levelshot in self.levelshot_int_list:
            if levelshot != "":
                # NB: This will extract the full path from within the archive.
                # Including the directory "levelshots".
                zipper.extract(levelshot, levelshot_extract_path)
                levelshot_file_path = os.path.join(levelshot_extract_path, levelshot)

                if is_non_html_image(levelshot_file_path):
                    levelshot_file_path = convert_image(levelshot_file_path, convert_image_format)

                self.levelshot_ext_list.append(levelshot_file_path)

        # if need be reorder levelshot_ext_list to correspond to levelshot_list's order
        levelshot_list_copy = self.levelshot_ext_list[:]

        if len(self.levelcode_list) > len(self.levelshot_ext_list):
            for i in range(len(self.levelcode_list) - len(self.levelshot_ext_list)):
                self.levelshot_ext_list.append("")

        for i, levelshot in enumerate(self.levelshot_int_list):
            levelshot_code = get_code_from_shot(levelshot)
            for k in range(len(self.levelcode_list)):
                # strip chars and lower
                levelshot_c = re.sub('[^0-9a-zA-Z]+', '', levelshot_code.lower())
                self_levelc = re.sub('[^0-9a-zA-Z]+', '', self.levelcode_list[k].lower())
                if levelshot_c == self_levelc:
                    self.levelshot_ext_list[k] = levelshot_list_copy[i]

        if self.is_mappack:
            # make sure that all lists are the same length or throw a warning
            if len(self.levelshot_int_list) != self.mapcount:
                if verbose:
                    print("warning the number of internal levelshots do not match the number of levels")
            if len(self.levelshot_ext_list) != self.mapcount:
                if verbose:
                    print("warning the number of external levelsohts do not match the number of levels")
            if len(self.longname_list) != self.mapcount:
                if verbose:
                    print("warning the number of longnames do not match the number of levels")
            if len(self.levelcode_list) != self.mapcount:
                if verbose:
                    print("warning the number of levelcodes do not match the number of levels")

        if len(self.longname_list) <= len(self.levelcode_list):
            for i in range(len(self.longname_list)):
                if self.longname_list[i] == "":
                    self.longname_list[i] = self.levelcode_list[i]


#####################


def parse_input_args(arguments):
    parser = argparse.ArgumentParser(description="Quake 3 map list html writer, \
            \n parses a directory of pk3 files and generates \
            a html page with titles and levelshots")

    parser.add_argument("-v", "--verbose", help="verbose output", action="store_true")

    parser.add_argument(
        "--output-dir",
        help="output directory",
        default=".",
        type=Path,
    )

    parser.add_argument(
        "--input-dir",
        type=Path,
        help="input directory with pk3 files"
    )

    parser.add_argument(
        "--temp-dir",
        help="temporary directory to extract level data generate \
            automatically but can be overwritten with this flag",
        type=Path,
        default=tempfile.mkdtemp(),
    )

    parser.add_argument(
        "--filter-scaled-warsow-maps",
        help="Omit multiple scales of the same warsow/warfork map.",
        action='store_true',
    )

    settings = parser.parse_args()
    settings.resource_path = Path(os.path.dirname(os.path.realpath(__file__))) / "resources"
    settings.levelshot_extract_path = settings.output_dir
    if settings.verbose:
        print(settings)

    return settings


def initialize_output_document(output_dir: Path, resource_path: Path, snippets):
    html_header_path = resource_path / "header.html"
    header_obj = open(html_header_path, "r")
    header = header_obj.read()
    shutil.copy(resource_path / "style.css", output_dir)
    shutil.copytree(resource_path / "images", output_dir / "images", dirs_exist_ok=True)

    output_obj = dummy_class()
    output_obj.path = os.path.join(output_dir, "index.html")
    Path(output_dir).mkdir(exist_ok=True)

    output_obj.text = open(output_obj.path, "w")

    output_obj.text.write(header)

    divider = snippets["divider_title"].format(
        image=os.path.join(resource_path, "images/online_icon.png"),
        title="kartor att spela",
        line1="dessa finns och spelas med angivet kommand",
        line2="",
    )

    output_obj.text.write(divider)
    return output_obj


def create_level_list(
    pk3_list,
    *,
    temp_dir: Path,
    levelshot_extract_path: Path,
    verbose: bool,
):
    # create a list of all levels from .pk3 files and `init` also extracts the levelshot
    level_list = []

    for pk3 in pk3_list:

        if verbose:
            print(f"creating level list from {pk3}")

        level = QuakeLevel()
        try:
            level.init(
                pk3,
                levelshot_extract_path=levelshot_extract_path,
                temporary_file_storage=temp_dir,
                verbose=verbose,
            )

            level_list.append(level)
        except zipfile.BadZipfile:
            if verbose:
                print(pk3 + " is not a valid pk3 file, skipping")

    return level_list


def generate_map_obj_from_level_list(level_list, verbose: bool, filter_scaled_warsow_maps: bool):
    added = set([])
    map_list = []
    for level in level_list:
        num_maps = level.mapcount

        for j in range(num_maps):
            map_obj = dummy_class()
            map_obj.levelcode = level.levelcode_list[j]
            base = map_obj.levelcode

            if j < len(level.longname_list):
                map_obj.longname = level.longname_list[j]
            else:
                if verbose:
                    print("warning no longname found in " + level.filename)
                map_obj.longname = map_obj.levelcode

            if j < len(level.levelshot_ext_list):
                map_obj.levelshot = level.levelshot_ext_list[j]
            else:
                if verbose:
                    print("warning missing levelshot for " + level.filename)
                map_obj.levelshot = ""

            if level.is_mappack:
                map_obj.title = map_obj.longname + "</b> in " + level.filename + "<b>"
            else:
                map_obj.title = map_obj.longname

            if map_obj.levelshot == '':  # and map_obj.is_mappack:  # DEBUG
                try:
                    map_obj.is_mappack
                except:
                    pass
                # Warsow bundles different scales of the same map as a map pack.
                # ['oxodm2a', 'oxodm2a_105', 'oxodm2a_110', 'oxodm2a_115', 'oxodm2a_120', 'oxodm2a_125', 'oxodm2a_130']
                # ['static/levelshots/oxodm2a.jpg', '', '', '', '', '', '']
                # If the map has an integer suffix we break this loop and go on
                # the next map.
                maybe_scaled = map_obj.levelcode.split('_')
                base = maybe_scaled[0]
                if len(maybe_scaled) == 2:
                    try:
                        int(maybe_scaled[1])
                        break
                    except ValueError:
                        pass

            if (not filter_scaled_warsow_maps) or (base not in added):
                added.add(base)
                map_list.append(map_obj)

    return map_list


def write_maps_to_output(
    output_obj,
    snippets,
    *,
    output_dir: Path,
    input_dir: Path,
    levelshot_extract_path: Path,  # TODO: do we really need two scratch dirs?
    temp_dir: Path,
    verbose: bool,
):
    num_brs = 21  # number of html line break tags needed between rows of floating "level containers"-divs
    pk3_list = glob.glob(input_dir.as_posix() + "/" + "*.pk3")

    assert len(pk3_list) > 0, f"Error: no maps found in input directory {input_dir}"
    level_list = create_level_list(
        pk3_list,
        temp_dir=temp_dir,
        levelshot_extract_path=levelshot_extract_path,
        verbose=verbose,
    )

    # level_title_file = os.path.join(output_dir, "level_titles.txt")
    # level_titles_obj = open(level_title_file, "r+")

    map_list = generate_map_obj_from_level_list(level_list, settings.verbose, settings.filter_scaled_warsow_maps)
    num_pk3s = len(pk3_list)

    if verbose:
        print("found " + str(num_pk3s) + " pk3 files \n")

    # NB(nils): if longnames are to be overwritten do it here
    # NB(nils): if levelshots are to be overwritten do it here

    for (map_index, map_obj) in enumerate(map_list):
        levelshot = Path(map_obj.levelshot)
        try:
            levelshot_path = levelshot.relative_to(settings.output_dir)
        except:
            # TODO: Removed duplicates from scaled warsow maps.
            # There is only a single levelshot but multiple maps.
            # oxodm2a{_105,_110,...}
            levelshot_path = Path("/dev/null")
        interim_title = snippets["level_body"].format(
            map=map_obj.title,
            comment="\\callvote map " + map_obj.levelcode,
            levelshot=levelshot_path,
        )
        output_obj.text.write(interim_title)

        # every second map, i e the right map out of two
        if map_index % 2 != 0:
            for k in range(num_brs):
                output_obj.text.write("<br/>")

    return output_obj


def write_output_footer(output_obj, resource_path: Path):
    # write some extra spacing after the last map
    num_brs = 21  # number of html line break tags needed between rows of floating "level containers"-divs
    for j in range(2 * num_brs):
        output_obj.text.write("<br/>")

    html_footer_path = resource_path / "footer.html"
    footer_obj = open(html_footer_path, "r")
    footer = footer_obj.read()
    output_obj.text.write(footer)
    return output_obj


def construct_html_snippets(resource_path: Path):
    snippets = {}

    html_divider_title_path = resource_path / "divider_title.html"
    html_divider_title = open(html_divider_title_path, 'r').read()
    snippets['divider_title'] = html_divider_title

    html_level_body_path = resource_path / "level_body.html"
    html_level_body = open(html_level_body_path, 'r').read()
    snippets['level_body'] = html_level_body

    return snippets


if __name__ == '__main__':
    settings = parse_input_args(sys.argv)
    snippets = construct_html_snippets(settings.resource_path)

    # TODO: must also move resources to the output.
    output_obj = initialize_output_document(
        settings.output_dir, settings.resource_path, snippets
    )

    output_obj = write_maps_to_output(
        output_obj,
        snippets,
        verbose=settings.verbose,
        output_dir=settings.output_dir,
        input_dir=settings.input_dir,
        temp_dir=settings.temp_dir,
        levelshot_extract_path=settings.levelshot_extract_path,
    )

    output_obj = write_output_footer(output_obj, settings.resource_path)

    # all open files are closed as the program terminates

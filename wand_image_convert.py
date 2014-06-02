from wand.image import Image

def convert_image(input_file_path, convert_format):

    output_file_path = input_file_path[:input_file_path.rfind('.')] + "." + convert_format
    print output_file_path
    with Image(filename = input_file_path) as img:
        print img.format
        with img.convert(convert_format) as conv:
            print conv.format
            img.save(filename=output_file_path)
            return output_file_path

if __name__ == '__main__':            
    convert_format = 'png'
    input_file_path = "/Users/Spill/Documents/programering/quakeTML/git/level_listing/images/quake/online/levelshots/13circle.tga"
    convert_image(input_file_path, convert_format)
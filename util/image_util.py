from PIL import Image, ImageFont, ImageDraw


# https://itnext.io/how-to-wrap-text-on-image-using-python-8f569860f89e
def text_wrap(text, font, max_width):
    """Wrap text base on specified width.
    This is to enable text of width more than the image width to be display
    nicely.

    @params:
        text: str
            text to wrap
        font: obj
            font of the text
        max_width: int
            width to split the text with
    @return
        lines: list[str]
            list of sub-strings
    """
    lines = []

    # If the text width is smaller than the image width, then no need to split
    # just add it to the line list and return
    if font.getsize(text)[0] <= max_width:
        lines.append(text)
    else:
        # split the line by spaces to get words
        words = text.split(' ')
        i = 0
        # append every word to a line while its width is shorter than the image width
        while i < len(words):
            line = ''
            while i < len(words) and font.getsize(line + words[i])[0] <= max_width:
                line = line + words[i] + " "
                i += 1
            if not line:
                line = words[i]
                i += 1
            lines.append(line)
    return lines


def resize(image, width):
    img_w = image.size[0]
    img_h = image.size[1]
    percent = width / float(img_w)
    size = int(float(img_h) * float(percent))
    rmg = image.resize((width, size), Image.ANTIALIAS)
    return rmg


def image_from_buffer(buffer):
    return Image.frombuffer("L", (4, 4), buffer, "raw", "L", 0, 1)


def stack_images(image1, image2):
    img2_h = image2.size[1]
    img2_w = image2.size[0]
    img1_h = image1.size[1]
    img1_w = image1.size[0]
    image2 = resize(image2, img1_w)
    image1.paste(image2, (int((img1_w / 2) - (img2_w / 2)), int((img1_h / 2) - (img2_h / 2))), image2)
    return image1

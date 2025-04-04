"""

RenderString

This class defines an object that uses TrueType fonts to render a string
to a PNG file (or other specified format).

The class should keep a list of fonts that it can use to render the string.
Fonts are added to the list by specifying the path to the font file, and 
subsequent calls to render strings will simply look up the font rather than
re-loading it each time.

"""

from PIL import Image, ImageDraw, ImageFont
import os

class StringRenderer:
    def __init__(self):
        self.fonts = {}

    def get_font(self, font_name, font_size=24):
        # The key is a tuple of font name and size.
        if (font_name, font_size) in self.fonts:
            return self.fonts[(font_name, font_size)]
        else:
            # Load the font from the windows font directory. This is a
            # little hacky under WSL, but Windows has a lot more fonts
            # installed by default than WSL.
            font_path = os.path.join("/mnt/c/Windows/Fonts", font_name)
            try:
                font = ImageFont.truetype(font_path, font_size)
                self.fonts[(font_name, font_size)] = font
            except IOError:
                print(f"Error loading font: {font_path}")

        return self.fonts[(font_name, font_size)]


    def render_string_to_png(self, text, font_name, font_size, color_triple, filename):
        font = self.get_font(font_name, font_size)
        text_bbox = font.getbbox(text)
        image = Image.new("RGBA", (text_bbox[2], text_bbox[3]), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.text((0, 0), text, fill=color_triple, font=font)
        image.save(filename, "PNG")


    def render_string_to_png_with_box(self, text, font_name, font_size, color_triple, filename):
        font = self.get_font(font_name, font_size)
        text_bbox = font.getbbox(text)

        image = Image.new("RGBA", (text_bbox[2] + 7, text_bbox[3] + 7), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.text((3, 3), text, fill=color_triple, font=font)

        # Draw a box around the text.
        draw.rectangle((0, 0, text_bbox[2] + 7, text_bbox[3] + 7), outline=color_triple, width=3)
        image.save(filename, "PNG")
        
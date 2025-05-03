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
import platform

class StringRenderer:
    def __init__(self):
        self.fonts = {}
        self.font_dir = ""
        if platform.system() == "Windows":
            # The font path is the Windows font directory.
            self.font_dir = os.path.join(os.environ["WINDIR"], "Fonts")
        elif platform.system() == "Linux":
            self.font_dir = "/mnt/c/Windows/Fonts"


    def get_font(self, font_name, font_size=24):
        # The key is a tuple of font name and size.
        if (font_name, font_size) in self.fonts:
            return self.fonts[(font_name, font_size)]
        else:
            # Load the font from the windows font directory. This is a
            # little hacky under WSL, but Windows has a lot more fonts
            # installed by default than WSL.
            font_path = os.path.join(self.font_dir, font_name)
            try:
                font = ImageFont.truetype(font_path, font_size)
                self.fonts[(font_name, font_size)] = font
            except IOError:
                print(f"Error loading font: {font_path}")

        return self.fonts[(font_name, font_size)]


    def render_string_to_png(self, text, font_name, font_size, font_color_triple, filename):
        font = self.get_font(font_name, font_size)
        text_bbox = font.getbbox(text)
        image = Image.new("RGBA", (text_bbox[2], text_bbox[3]), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.text((0, 0), text, fill=font_color_triple, font=font)
        image.save(filename, "PNG")

    # Draw the string such that the lower left corner of the text is at the center of the
    # image, plus a little offset so that the text doesn't sit on top of the center point.
    def render_string_to_png_offset(self, text, font_name, font_size, font_color_triple, filename):
        # Render the string such that the string begins in the center of the image.
        font = self.get_font(font_name, font_size)
        text_bbox = font.getbbox(text)

        padding = 5

        offset_x = text_bbox[2] - text_bbox[0]
        offset_y = ((text_bbox[3] - text_bbox[1]) // 2)

        # Size the image so that it is wide enough to hold the text plus the offset.
        image = Image.new("RGBA", 
                          size = (text_bbox[2] + offset_x + padding, text_bbox[3] + offset_y + padding), 
                          color = (0,0,0,0))
        draw = ImageDraw.Draw(image)

        # Where this is drawn is a little wonky. I think 0,0 is the LLC for the image but
        # the text is drawn from the ULC. But it's like 6:30AM on a Saturday and I don't
        # want to figure it out right now.
        draw.text((offset_x + (padding // 2), -(offset_y // 2)), 
                  text, fill=font_color_triple, font=font)
        image.save(filename, "PNG")


    def render_string_to_png_with_box(self, text, font_name, font_size, font_color_triple, filename):
        font = self.get_font(font_name, font_size)
        text_bbox = font.getbbox(text)

        image = Image.new("RGBA", (text_bbox[2] + 7, text_bbox[3] + 7), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.text((3, 3), text, fill=font_color_triple, font=font)

        # Draw a box around the text.
        draw.rectangle((0, 0, text_bbox[2] + 7, text_bbox[3] + 7), outline=font_color_triple, width=3)
        image.save(filename, "PNG")

# Test harness.

if __name__ == "__main__":
    renderer = StringRenderer()
    # Test rendering a string to a PNG file.
    renderer.render_string_to_png("Hello, World!", "arial.ttf", 72, (255, 0, 0), "test.png")
    renderer.render_string_to_png_offset("Centered Text", "arial.ttf", 72, (0, 255, 0), "test_offset.png")
    renderer.render_string_to_png_with_box("Boxed Text", "arial.ttf", 72, (0, 0, 255), "test_boxed.png")
    
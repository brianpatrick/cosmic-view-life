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


    def _measure_text(self, text, font):
        """Returns (left, top, right, bottom) bounding box for text, handling newlines."""
        temp = Image.new("RGBA", (1, 1))
        draw = ImageDraw.Draw(temp)
        return draw.multiline_textbbox((0, 0), text, font=font)

    def render_string_to_png(self, text, font_name, font_size, font_color_triple, filename):
        font = self.get_font(font_name, font_size)
        text_bbox = self._measure_text(text, font)
        w = text_bbox[2] - text_bbox[0]
        h = text_bbox[3] - text_bbox[1]
        image = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.multiline_text((-text_bbox[0], -text_bbox[1]), text, fill=font_color_triple, font=font)
        image.save(filename, "PNG")

    # Draw the string such that the lower left corner of the text is at the center of the
    # image. When composited onto a scene, the image center aligns with the labeled object,
    # so the text extends to the upper-right of that point.
    def render_string_to_png_offset(self, text, font_name, font_size, font_color_triple, filename,
                                    background_color=(0, 0, 0, 0)):
        font = self.get_font(font_name, font_size)
        text_bbox = self._measure_text(text, font)

        padding = 5
        w = text_bbox[2] - text_bbox[0]
        h = text_bbox[3] - text_bbox[1]

        # The image is 2w wide and 2h tall so that the center pixel is the anchor point.
        # The text occupies the upper-right quadrant: left edge at center_x, bottom at center_y.
        center_x = w + padding // 2
        center_y = h + padding // 2
        image = Image.new("RGBA",
                          size=(2 * w + padding, 2 * h + padding),
                          color=background_color)
        draw = ImageDraw.Draw(image)

        draw_x = center_x - text_bbox[0]
        draw_y = center_y - text_bbox[3]
        draw.multiline_text((draw_x, draw_y), text, fill=font_color_triple, font=font)
        image.save(filename, "PNG")


    def render_string_to_png_with_box(self, text, font_name, font_size, font_color_triple, filename,
                                      background_color=(0, 0, 0, 0)):
        font = self.get_font(font_name, font_size)
        text_bbox = self._measure_text(text, font)

        w = text_bbox[2] - text_bbox[0]
        h = text_bbox[3] - text_bbox[1]

        image = Image.new("RGBA", (w + 7, h + 7), background_color)
        draw = ImageDraw.Draw(image)
        draw.multiline_text((3 - text_bbox[0], 3 - text_bbox[1]), text, fill=font_color_triple, font=font)

        # Draw a box around the text.
        draw.rectangle((0, 0, w + 6, h + 6), outline=font_color_triple, width=3)
        image.save(filename, "PNG")

# Test harness.

if __name__ == "__main__":
    renderer = StringRenderer()
    # Test rendering a string to a PNG file.
    renderer.render_string_to_png("Hello World!\nSecond Line", "BRITANIC.TTF", 72, (255, 0, 0), "test.png")
    renderer.render_string_to_png_offset("Viridiplantae (32)\nSubtitle", "BRITANIC.TTF", 72, (0, 255, 0), "test_offset.png",
                                         background_color=(25, 25, 25, 255))
    renderer.render_string_to_png_with_box("Boxed Text\nLine 2", "BRITANIC.TTF", 72, (0, 0, 255), "test_boxed.png")
    
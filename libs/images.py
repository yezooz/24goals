from PIL import Image
import os.path

from cStringIO import StringIO


class ImageProcessing():
    def thumbnail(self, filename, size=(50, 50), output_filename=None):
        image = Image.open(filename)
        if image.mode not in ('L', 'RGB'):
            image = image.convert('RGB')
        image = image.resize(size, Image.ANTIALIAS)

        # get the thumbnail data in memory.
        if not output_filename:
            output_filename = get_default_thumbnail_filename(output_filename)
        image.save(output_filename, image.format)
        return output_filename

    def thumbnail_string(self, buf, size=(50, 50)):
        f = StringIO.StringIO(buf)
        image = Image.open(f)
        if image.mode not in ('L', 'RGB'):
            image = image.convert('RGB')
        image = image.resize(size, Image.ANTIALIAS)
        o = StringIO.StringIO()
        image.save(o, "JPEG")
        return o.getvalue()

    def get_default_thumbnail_filename(self, filename):
        path, ext = os.path.splitext(filename)
        return path + '.thumb.jpg'

    def rescale(self, data, width, height, force=True):
        """Rescale the given image, optionally cropping it to make sure the result image has the specified width and height."""
        import Image as pil
        from cStringIO import StringIO

        max_width = width
        max_height = height

        input_file = StringIO(data)
        img = pil.open(input_file)
        img = img.convert('RGB')

        if not force:
            img.thumbnail((max_width, max_height), pil.ANTIALIAS)
        else:
            src_width, src_height = img.size
            src_ratio = float(src_width) / float(src_height)
            dst_width, dst_height = max_width, max_height
            dst_ratio = float(dst_width) / float(dst_height)

            if dst_ratio < src_ratio:
                crop_height = src_height
                crop_width = crop_height * dst_ratio
                x_offset = float(src_width - crop_width) / 2
                y_offset = 0
            else:
                crop_width = src_width
                crop_height = crop_width / dst_ratio
                x_offset = 0
                y_offset = float(src_height - crop_height) / 3
            img = img.crop(
                (int(x_offset), int(y_offset), int(x_offset) + int(crop_width), int(y_offset) + int(crop_height)))
            img = img.resize((dst_width, dst_height), pil.ANTIALIAS)

        tmp = StringIO()
        img.save(tmp, 'JPEG')
        tmp.seek(0)
        output_data = tmp.getvalue()
        input_file.close()
        tmp.close()

        return output_data


if __name__ == '__main__':
    pass

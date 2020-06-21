from __future__ import absolute_import
from PIL import Image, ImageDraw

from qrcode import QRCode, constants
from qrcode.image.base import BaseImage

class CashyFactory(BaseImage):
    """
    Cashy QR image builder, default format is PNG.
    """
    kind = "PNG"

    def new_image(self, **kwargs):
        self.back_color = kwargs.get("back_color", "white").lower()
        self.fill_color = kwargs.get("fill_color", "black").lower()
        if self.back_color == "transparent":
            mode = "RGBA"
            self.back_color = None
        else:
            mode = "RGB"

        # Create base image
        img = Image.new(
            mode,
            (self.pixel_size, self.pixel_size),
            self.back_color
        )
        self._idr = ImageDraw.Draw(img)

        # Create base mask
        self._cqr_antialias = 8
        self._cqr_mask_color = "black"
        self._cqr_inverse_mask_color = "white"
        # Use a single channel image as mask and increase mask size to get smoother results
        self._cqr_mask = Image.new(
            size=[int(dim * self._cqr_antialias) for dim in img.size],
            mode="L",
            color=self._cqr_mask_color
        )
        self._cqr_mask_draw = ImageDraw.Draw(self._cqr_mask)

        # Create logo image
        logo_path = kwargs.get("logo_path", None)
        self.logo_image = None
        if logo_path:
            logo_image = Image.open(logo_path)
            background = Image.new(
                mode,
                (int(self.pixel_size*0.3) -1, int(self.pixel_size*0.3) -1),
                self.back_color
            )
            background.paste(logo_image, ((background.size[0] - logo_image.size[0]) // 2, (background.size[1] - logo_image.size[1]) // 2))
            self.logo_image = background

        return img

    def drawrect(self, row, col):
        bounds = self.pixel_box(row, col)
        type = self._compute_postype(bounds)
        # Decrease box size to get smoother results and apply masked shapes
        if type == "posrow-t":
            bounds[0] = (bounds[0][0], bounds[0][1] + 1)
            self._idr.rectangle(bounds, fill=self.fill_color)
        elif type == "posrow-r":
            bounds[1] = (bounds[1][0] - 1, bounds[1][1])
            self._idr.rectangle(bounds, fill=self.fill_color)
        elif type == "posrow-b":
            bounds[1] = (bounds[1][0], bounds[1][1] - 1)
            self._idr.rectangle(bounds, fill=self.fill_color)
        elif type == "posrow-l":
            bounds[0] = (bounds[0][0] + 1, bounds[0][1])
            self._idr.rectangle(bounds, fill=self.fill_color)
        elif type == "poscorner-tl":
            bounds[0] = (bounds[0][0] + 2, bounds[0][1] + 2)
            bounds[1] = (bounds[1][0] + self.box_size - 2, bounds[1][1] + self.box_size - 2)
            self._mask_pieslice(bounds, 90, 360, width=2)
        elif type == "poscorner-tr":
            bounds[0] = (bounds[0][0] - self.box_size + 2, bounds[0][1] + 2)
            bounds[1] = (bounds[1][0] - 1, bounds[1][1] + self.box_size - 1)
            self._mask_pieslice(bounds, 180, 90, width=2)
        elif type == "poscorner-bl":
            bounds[0] = (bounds[0][0] + 2, bounds[0][1] - self.box_size + 2)
            bounds[1] = (bounds[1][0] + self.box_size - 1, bounds[1][1] - 1)
            self._mask_pieslice(bounds, 0, 270, width=2)
        elif type == "poscorner-br":
            bounds[0] = (bounds[0][0] - self.box_size + 2, bounds[0][1] - self.box_size + 2)
            bounds[1] = (bounds[1][0] - 1, bounds[1][1] - 1)
            self._mask_pieslice(bounds, 270, 180, width=2)
        elif type == "posquare":
            self._idr.rectangle(bounds, fill=self.fill_color)
        elif type == "module":
            bounds[0] = (bounds[0][0] + 1, bounds[0][1] + 1)
            bounds[1] = (bounds[1][0] - 1, bounds[1][1] - 1)
            self._mask_ellipse(bounds)

    def _mask_ellipse(self, bounds, width=1):
        for offset, fill in (width/-2.0, self._cqr_inverse_mask_color), (width/2.0, self._cqr_inverse_mask_color):
            left, top = [(value + offset) * self._cqr_antialias for value in bounds[0]]
            right, bottom = [(value - offset) * self._cqr_antialias for value in bounds[1]]
            self._cqr_mask_draw.ellipse([left, top, right, bottom], fill=fill)

    def _mask_pieslice(self, bounds, angstart, angend, width=1):
        for offset, fill in (width/-2.0, self._cqr_inverse_mask_color), (width/2.0, self._cqr_inverse_mask_color):
            left, top = [(value + offset) * self._cqr_antialias for value in bounds[0]]
            right, bottom = [(value - offset) * self._cqr_antialias for value in bounds[1]]
            self._cqr_mask_draw.pieslice([left, top, right, bottom], angstart, angend, fill=fill)
    
    def _compute_postype(self, bounds):
        x = bounds[0][0]
        y = bounds[0][1]
        # Ignore 4th finder pattern
        if not (x >= self.pixel_size - 7*self.box_size and y >= self.pixel_size - 7*self.box_size):

            if (x <= 7*self.box_size or x >= self.pixel_size - 7*self.box_size) and (y == 0 or y == self.pixel_size - 7*self.box_size):
                if x == 0 or x == self.pixel_size - 7*self.box_size:
                   return "poscorner-tl"
                if x == 6*self.box_size or x == self.pixel_size - 1*self.box_size:
                   return "poscorner-tr"
                return "posrow-t"
            
            if (x <= 7*self.box_size or x >= self.pixel_size - 7*self.box_size) and (y == 6*self.box_size or y == self.pixel_size - 1*self.box_size):
                if x == 0 or x == self.pixel_size - 7*self.box_size:
                   return "poscorner-bl"
                if x == 6*self.box_size or x == self.pixel_size - 1*self.box_size:
                   return "poscorner-br"
                return "posrow-b"

            if (y <= 7*self.box_size or y >= self.pixel_size - 7*self.box_size) and (x == 0 or x == self.pixel_size - 7*self.box_size):
                return "posrow-l"

            if (y <= 7*self.box_size or y >= self.pixel_size - 7*self.box_size) and (x == 6*self.box_size or x == self.pixel_size - 1*self.box_size):
                return "posrow-r"

            # Inner finder patterns
            if (x <= 5*self.box_size or x >= self.pixel_size - 5*self.box_size) and (y == 2*self.box_size or y == self.pixel_size - 5*self.box_size):
                if x == 2*self.box_size or x == self.pixel_size - 5*self.box_size:
                   return "poscorner-tl"
                if x == 4*self.box_size or x == self.pixel_size - 3*self.box_size:
                   return "poscorner-tr"
                return "posrow-t"
            
            if (x <= 5*self.box_size or x >= self.pixel_size - 5*self.box_size) and (y == 4*self.box_size or y == self.pixel_size - 3*self.box_size):
                if x == 2*self.box_size or x == self.pixel_size - 5*self.box_size:
                   return "poscorner-bl"
                if x == 4*self.box_size or x == self.pixel_size - 3*self.box_size:
                   return "poscorner-br"
                return "posrow-b"

            if (y <= 5*self.box_size or y >= self.pixel_size - 5*self.box_size) and (x == 2*self.box_size or x == self.pixel_size - 5*self.box_size):
                return "posrow-l"

            if (y <= 5*self.box_size or y >= self.pixel_size - 5*self.box_size) and (x == 4*self.box_size or x == self.pixel_size - 3*self.box_size):
                return "posrow-r"

            if (x == 3*self.box_size and y == 3*self.box_size) or (x == self.pixel_size - 4*self.box_size and y == 3*self.box_size) or (x == 3*self.box_size and y == self.pixel_size - 4*self.box_size):
                return "posquare"

        return "module"

    def save(self, stream, format=None, quality=95, **kwargs):
        # Downsample the mask using LANCZOS algorithm
        self._cqr_mask = self._cqr_mask.resize(self._img.size, Image.LANCZOS)
        # Apply mask to the image
        self._img.paste(self.fill_color, mask=self._cqr_mask)
        # Paste logo on center
        if self.logo_image:
            self._img.paste(self.logo_image, ((self._img.size[0] - self.logo_image.size[0]) // 2, (self._img.size[1] - self.logo_image.size[1]) // 2))
        # Save image
        if format is None:
            format = kwargs.get("kind", self.kind)
        if "kind" in kwargs:
            del kwargs["kind"]
        self._img.save(stream, format=format, quality=quality, **kwargs)

    def __getattr__(self, name):
        return getattr(self._img, name)

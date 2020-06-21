# cashy-qr
Cash-like inspired QR codes

### From
![From QR](from.png)

### To
![To QR](to.png)

*__Notice!__* this repository is still in development and there are several important code/looks enhancements.

# Requirements
`qrcode>=6.1` with `Pillow>=6.1.0`

# Usage
This filter is just an image factory extension for the `qrcode` python library, example:
```python
qr = QRCode(
    version=5,
    error_correction=constants.ERROR_CORRECT_H, # Compulsory if using logo
    box_size=10,
    border=0, # Compulsory 0, (TODO)
    image_factory=CashyFactory,
    mask_pattern=None
)
qr.add_data("<>") # With version 5 up to 64 chars
im = qr.make_image(
    fit=False,
    back_color="white",
    fill_color="black",
    logo_path=r"<>.png" # Provide (if wanted) a resized logo because I cannot get Pillow to mantain quality while resizing it
)
im.save("<>.png", format="PNG")
im.show()
```

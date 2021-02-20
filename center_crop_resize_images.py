import os
from PIL import Image

def center_crop(im):
    width, height = im.size
    if width < height:
        a = 0
        b = (height - width) // 2
        c = width
        d = height - b
        return im.crop((a, b, c, d))
    else:
        a = (width - height) // 2
        b = 0
        c = width - a
        d = height
        return im.crop((a, b, c, d))
    
for image in os.listdir('images'):
    try:
        if '.jpg' in image:
            im = Image.open(f"images/{image}")
            im1 = center_crop(im)
            im1 = im1.resize((200, 200))
            im1.save(f"images_resized/{image}")
    except:
        print(image)

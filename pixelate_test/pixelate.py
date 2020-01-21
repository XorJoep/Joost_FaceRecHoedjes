from PIL import Image
import numpy as np

im_frame = Image.open('selfie.png')

image_in = np.array(im_frame)
new_image = np.empty_like(image_in)

(face_x, face_y, face_w, face_h) = (235, 75, 140, 160)

pixel_buffer = [0] * 32

blocksize = 8

for y in range(im_frame.height):
	for x in range(im_frame.width):

		dr = image_in[y][x]

		if x >= face_x and x <= face_x + face_w and y >= face_y and y <= face_y + face_h:
			if (x-face_x) % blocksize == 0 and (y-face_y) % blocksize == 0:
				pixel_buffer[(x-face_x)//blocksize] = dr
				dn = dr
			else:
				dn = pixel_buffer[(x-face_x)//blocksize]
		else:
			dn = dr

		new_image[y][x] = dn

img_out = Image.fromarray(new_image)
im_frame.show()
img_out.show()
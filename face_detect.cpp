#include <stdint.h>
#include <hls_stream.h>
#include <ap_axi_sdata.h>

#define WIDTH 1280
#define HEIGHT 720

#define BLOCKSIZE 8
#define BUFFERSIZE WIDTH / BLOCKSIZE
#define RED 0xFF0000 

typedef ap_axiu<32,1,1,1> pixel_data;
typedef hls::stream<pixel_data> pixel_stream;

void face_detect(pixel_stream &src, pixel_stream &dst, 
	uint16_t face_x, uint16_t face_y, uint16_t face_w, uint16_t face_h, 
	uint8_t mode)
{
	#pragma HLS pipeline

	#pragma HLS INTERFACE ap_ctrl_none port=return
	#pragma HLS INTERFACE axis port=&src
	#pragma HLS INTERFACE axis port=&dst
	#pragma HLS INTERFACE s_axilite port=face_x
	#pragma HLS INTERFACE s_axilite port=face_y
	#pragma HLS INTERFACE s_axilite port=face_w
	#pragma HLS INTERFACE s_axilite port=face_h
	#pragma HLS INTERFACE s_axilite port=mode

	// Data to be stored across 'function calls'
	static uint16_t x = 0;
	static uint16_t y = 0;
	static pixel_data pixel_buffer[BUFFERSIZE] = {};

	// pixels in and out
	static pixel_data pixel_out;
	pixel_data pixel_in;
	src >> pixel_in;

	pixel_out = pixel_in;

	// Reset X and Y counters on user signal
	if (pixel_in.user)
		x = y = 0;

	switch (mode) {
		case 0:
			// Change nothing
			break;
		case 1:
			// Show face with a rectangle
			if (x == face_x || x == face_x + face_w // pixel is within face
			  || y == face_y || y == face_y + face_h ) {
				pixel_out.data = RED;
			}
			break;
		case 2:
			// Pixelate
			if (x >= face_x && x <= face_x + face_w // pixel is within face
			 && y >= face_y && y <= face_y + face_h ) {
				if ((y-face_y) % BLOCKSIZE == 0 // first row of block
				 && (x-face_x) % BLOCKSIZE == 0) { // first column of block
					pixel_buffer[(x-face_x)/BLOCKSIZE] = pixel_in; // store pixel
				}
				else if ((x-face_x) % BLOCKSIZE == 0) { // first pixel of new row
					pixel_out = pixel_buffer[(x-face_x)/BLOCKSIZE]; // load pixel data for row
				}
			}
			break;
		default:
			// change nothing
			break;
	}

	////////////////////////////////

	// Write pixel to destination
	dst << pixel_out;

	// Increment X and Y counters
	if (pixel_in.last) {
		x = 0;
		y++;
	}
	else
		x++;
}


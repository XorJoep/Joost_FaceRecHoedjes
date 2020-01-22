#include <stdint.h>
#include <hls_stream.h>
#include <ap_axi_sdata.h>

#define WIDTH 1280
#define HEIGHT 720

#define WINDOW_SIZE 3
#define HALF_SIZE (((WINDOW_SIZE) - 1) / 2)

#define GR(v) ((v)&0xFF)
#define GG(v) (((v)&0xFF00)>>8)
#define GB(v) (((v)&0xFF0000)>>16)
#define SR(v) ((v)&0xFF)
#define SG(v) (((v)&0xFF)<<8)
#define SB(v) (((v)&0xFF)<<16)

typedef ap_axiu<32,1,1,1> pixel_data;
typedef hls::stream<pixel_data> pixel_stream;

const uint8_t kernel[WINDOW_SIZE][WINDOW_SIZE] = 
	{
		1, 2, 1, 
		2, 4, 2, 
		1, 2, 1
	};

inline bool within_face(uint16_t x, uint16_t y,
	uint16_t face_x, uint16_t face_y, uint16_t face_w, uint16_t face_h)
{
	return x >= face_x && x <= face_x + face_w && y >= face_y && y <= face_y + face_h;
}

inline uint32_t blur(uint32_t window[WINDOW_SIZE][WINDOW_SIZE], 
	uint16_t x, uint16_t y,
	uint16_t face_x, uint16_t face_y, uint16_t face_w, uint16_t face_h )
{
	uint16_t sum_red = 0;
	uint16_t sum_green = 0;
	uint16_t sum_blue = 0;
	for (uint8_t i = -HALF_SIZE; i <= HALF_SIZE; i++)
		#pragma HLS PIPELINE
		for (uint8_t j = -HALF_SIZE; j <= HALF_SIZE; j++)
			#pragma HLS PIPELINE
			if (within_face(x + i, y + j, face_x, face_y, face_w, face_h)) {
				uint8_t k_val = kernel[i + HALF_SIZE][j + HALF_SIZE];
				uint32_t pixel = window[i + HALF_SIZE][j + HALF_SIZE];
				sum_red += GR(pixel) * k_val;
				sum_green += GG(pixel) * k_val;
				sum_blue += GB(pixel) * k_val;
			}
	return SR(sum_red / 16) + SG(sum_green / 16) + SB(sum_blue / 16);
}


void face_blurrer(pixel_stream &src, pixel_stream &dst, 
	uint16_t face_x, uint16_t face_y, uint16_t face_w, uint16_t face_h, 
	uint8_t switch_is_on)
{
	#pragma HLS INTERFACE ap_ctrl_none port=return
	#pragma HLS INTERFACE axis port=&src
	#pragma HLS INTERFACE axis port=&dst
	#pragma HLS INTERFACE s_axilite port=face_x
	#pragma HLS INTERFACE s_axilite port=face_y
	#pragma HLS INTERFACE s_axilite port=face_w
	#pragma HLS INTERFACE s_axilite port=face_h
	#pragma HLS INTERFACE s_axilite port=switch_is_on

	#pragma HLS PIPELINE

	// Data to be stored across 'function calls'
	static uint16_t x = 0;
	static uint16_t y = 0;

	uint32_t pixel_in;
	uint32_t pixel_out;

	static uint32_t line_buf[WINDOW_SIZE - 1][WIDTH]; // matrix buffering pixeldata
	static uint32_t window[WINDOW_SIZE][WINDOW_SIZE];
	static uint32_t right[WINDOW_SIZE];
	#pragma HLS ARRAY_PARTITION variable=line_buf complete dim=1
	#pragma HLS ARRAY_PARTITION variable=window complete dim=0
	#pragma HLS ARRAY_PARTITION variable=right complete

		// Load initial values into line buffer
	uint32_t read_count = WIDTH * HALF_SIZE + HALF_SIZE + 1;

	pixel_data p_in;
	pixel_data p_out;

	src >> p_in;
	pixel_in = p_in.data;

	if (y < WINDOW_SIZE - 1) { // Fill a buffer for the window
		
		line_buf[y][x] = pixel_in;
		pixel_out = pixel_in;
	}
	else {

		// Compute outgoing pixel data
		switch (switch_is_on) {
			case 0:
				pixel_out = pixel_in;
				break;
			case 1:
				if (within_face(x, y, face_x, face_y, face_w, face_y)) {
					pixel_out = blur(window, x, y)
				}
				break;
			case 2:
				// Horizontale pixel out
				break;
			case 3:
				// pixelate blok
				break;
			case 4:
				// blok pixel met blur
				break;
			default:
				break;
		}

		// Shift line buffer column up
		right[0] = line_buf[0][x];
		for (int y = 1; y < WINDOW_SIZE - 1; y++) {
			right[y] = line_buf[y - 1][x] = line_buf[y][x];
		}

		right[WINDOW_SIZE - 1] = line_buf[WINDOW_SIZE - 2][x] = pixel_in;

		// Shift window left
		for (int y = 0; y < WINDOW_SIZE; y++) {
			for (int x = 0; x < WINDOW_SIZE - 1; x++) {
				window[y][x] = window[y][x + 1];
			}
		}

		// Update rightmost window values
		for (int y = 0; y < WINDOW_SIZE; y++) {
			window[y][WINDOW_SIZE - 1] = right[y];
		}
	}

	p_out.data = pixel_out;
	dst << p_out;

	// Increment X and Y counters
	if (p_in.last)
	{
			x = 0;
			y++;
	}
	else
			x++;
	}

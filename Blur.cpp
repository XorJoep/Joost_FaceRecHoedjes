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
		for (uint8_t j = -HALF_SIZE; j <= HALF_SIZE; j++)
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

	// Data to be stored across 'function calls'
	static uint16_t x = 0;
	static uint16_t y = 0;

	uint32_t pixel_in;
	uint32_t pixel_out;
	uint32_t line_buf[WINDOW_SIZE - 1][WIDTH]; // matrix buffering pixeldata

	  // Load initial values into line buffer
	uint32_t read_count = WIDTH * HALF_SIZE + HALF_SIZE + 1;
	buf_x1 : for (int x = WIDTH - HALF_SIZE - 1; x < WIDTH; x++)
		#pragma HLS PIPELINE
		line_buf[HALF_SIZE - 1][x] = src.read();
		buf_y : for (int y = HALF_SIZE; y < WIN_SIZE - 1; y++)
			buf_x2 : for (int x = 0; x < WIDTH; x++)
				#pragma HLS PIPELINE
				// line_buf[y][x] = in_stream.read();
				src >> line_buf[y][x]


	pixel_data p_in;

	// Load input data from source
	src >> p_in;

	////////////////////////////////

	// Pixel data to be stored across 'function calls'
	// static pixel_data p_out = p_in;
	//static uint32_t dl = 0;
	//static uint32_t dc = 0;

	// Current (incoming) pixel data
	uint32_t pixel_in = p_in.data;

	// Compute outgoing pixel data
	swith (mode) {
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

	p_out.data = dn;

	////////////////////////////////

	// Write pixel to destination
	dst << p_out;

	// Copy previous pixel data to next output pixel
	p_out = p_in;

	// Increment X and Y counters
	if (p_in.last)
	{
			x = 0;
			y++;
	}
	else
			x++;
}

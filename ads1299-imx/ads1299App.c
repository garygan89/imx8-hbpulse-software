/**
 * Main application file to communicate with ADS1299 on Intel Edison.
 *
 * Uses the following settings:
 * Internal Test Signals
 * Test Signal Amplitude: VREFP-VREFN/2.4
 * Test Signal Frequency: 2Hz (f(CLK)/2^20)
 * Channel Input: Test Signal
 * PGA Gain: 24
 */

/*
 * SPI testing utility (using spidev driver)
 *
 * Copyright (c) 2007  MontaVista Software, Inc.
 * Copyright (c) 2007  Anton Vorontsov <avorontsov@ru.mvista.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License.
 *
 * Cross-compile with cross-gcc -I/path/to/cross-kernel/include
 */

#include <stdint.h>
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <getopt.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/ioctl.h>
#include <sys/stat.h>
#include <linux/types.h>
#include <linux/spi/spidev.h>

// ads1299 REG
// device settings
# define ID  0x00

// global settings
# define CONFIG1  0x01
# define CONFIG2  0x02
# define CONFIG3  0x03
# define LOFF  0x04

// channel specific settings
# define CHnSET  0x04
# define CH1SET  CHnSET + 1
# define CH2SET  CHnSET + 2
# define CH3SET  CHnSET + 3
# define CH4SET  CHnSET + 4
# define CH5SET  CHnSET + 5
# define CH6SET  CHnSET + 6
# define CH7SET  CHnSET + 7
# define CH8SET  CHnSET + 8
//	RLD_SENSP  0x0d
//	RLD_SENSN  0x0e
# define BIASSENSP  0x0d
# define BIASSENSN  0x0e
# define LOFF_SENSP  0x0f
# define LOFF_SENSN  0x10
# define LOFF_FLIP  0x11

// lead off status
# define LOFF_STATP  0x12
# define LOFF_STATN  0x13

// other
# define GPIO  0x14
# define PACE  0x15 // also MISC1
# define MISC1  0x15
# define RESP  0x16 // also MISC2
# define MISC2  0x16
# define CONFIG4  0x17
# define WCT1  0x18
# define WCT2  0x19

# define SPI_RESET 0x06

#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))

static void pabort(const char *s)
{
	perror(s);
	abort();
}

static const char *device = "/dev/spidev0.0";
static uint32_t mode;
static uint8_t bits = 8;
static char *input_file;
static char *output_file;
static uint32_t speed = 500000;
static uint16_t delay;
static int verbose;

uint8_t default_tx[] = {
	0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
	0x40, 0x00, 0x00, 0x00, 0x00, 0x95,
	0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
	0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
	0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
	0xF0, 0x0D,
};

uint8_t default_rx[ARRAY_SIZE(default_tx)] = {0, };
char *input_tx;

static void hex_dump(const void *src, size_t length, size_t line_size,
		     char *prefix)
{
	int i = 0;
	const unsigned char *address = src;
	const unsigned char *line = address;
	unsigned char c;

	printf("%s | ", prefix);
	while (length-- > 0) {
		printf("%02X ", *address++);
		if (!(++i % line_size) || (length == 0 && i % line_size)) {
			if (length == 0) {
				while (i++ % line_size)
					printf("__ ");
			}
			printf(" | ");  /* right close */
			while (line < address) {
				c = *line++;
				printf("%c", (c < 33 || c == 255) ? 0x2E : c);
			}
			printf("\n");
			if (length > 0)
				printf("%s | ", prefix);
		}
	}
}

/*
 *  Unescape - process hexadecimal escape character
 *      converts shell input "\x23" -> 0x23
 */
static int unescape(char *_dst, char *_src, size_t len)
{
	int ret = 0;
	int match;
	char *src = _src;
	char *dst = _dst;
	unsigned int ch;

	while (*src) {
		if (*src == '\\' && *(src+1) == 'x') {
			match = sscanf(src + 2, "%2x", &ch);
			if (!match)
				pabort("malformed input string");

			src += 4;
			*dst++ = (unsigned char)ch;
		} else {
			*dst++ = *src++;
		}
		ret++;
	}
	return ret;
}

static void transfer(int fd, uint8_t const *tx, uint8_t const *rx, size_t len)
{
	int ret;
	int out_fd;
	struct spi_ioc_transfer tr = {
		.tx_buf = (unsigned long)tx,
		.rx_buf = (unsigned long)rx,
		.len = len,
		.delay_usecs = delay,
		.speed_hz = speed,
		.bits_per_word = bits,
	};

	if (mode & SPI_TX_QUAD)
		tr.tx_nbits = 4;
	else if (mode & SPI_TX_DUAL)
		tr.tx_nbits = 2;
	if (mode & SPI_RX_QUAD)
		tr.rx_nbits = 4;
	else if (mode & SPI_RX_DUAL)
		tr.rx_nbits = 2;
	if (!(mode & SPI_LOOP)) {
		if (mode & (SPI_TX_QUAD | SPI_TX_DUAL))
			tr.rx_buf = 0;
		else if (mode & (SPI_RX_QUAD | SPI_RX_DUAL))
			tr.tx_buf = 0;
	}

	ret = ioctl(fd, SPI_IOC_MESSAGE(1), &tr);
	if (ret < 1)
		pabort("can't send spi message");

	if (verbose)
		hex_dump(tx, len, 32, "TX");

	if (output_file) {
		out_fd = open(output_file, O_WRONLY | O_CREAT | O_TRUNC, 0666);
		if (out_fd < 0)
			pabort("could not open output file");

		ret = write(out_fd, rx, len);
		if (ret != len)
			pabort("not all bytes written to output file");

		close(out_fd);
	}

	if (verbose || !output_file)
		hex_dump(rx, len, 32, "RX");
}

static void print_usage(const char *prog)
{
	printf("Usage: %s [-DsbdlHOLC3]\n", prog);
	puts("  -D --device   device to use (default /dev/spidev0.0)\n"
	     "  -s --speed    max speed (Hz)\n"
	     "  -d --delay    delay (usec)\n"
	     "  -b --bpw      bits per word\n"
	     "  -i --input    input data from a file (e.g. \"test.bin\")\n"
	     "  -o --output   output data to a file (e.g. \"results.bin\")\n"
	     "  -l --loop     loopback\n"
	     "  -H --cpha     clock phase\n"
	     "  -O --cpol     clock polarity\n"
	     "  -L --lsb      least significant bit first\n"
	     "  -C --cs-high  chip select active high\n"
	     "  -3 --3wire    SI/SO signals shared\n"
	     "  -v --verbose  Verbose (show tx buffer)\n"
	     "  -p            Send data (e.g. \"1234\\xde\\xad\")\n"
	     "  -N --no-cs    no chip select\n"
	     "  -R --ready    slave pulls low to pause\n"
	     "  -2 --dual     dual transfer\n"
	     "  -4 --quad     quad transfer\n");
	exit(1);
}

static void parse_opts(int argc, char *argv[])
{
	while (1) {
		static const struct option lopts[] = {
			{ "device",  1, 0, 'D' },
			{ "speed",   1, 0, 's' },
			{ "delay",   1, 0, 'd' },
			{ "bpw",     1, 0, 'b' },
			{ "input",   1, 0, 'i' },
			{ "output",  1, 0, 'o' },
			{ "loop",    0, 0, 'l' },
			{ "cpha",    0, 0, 'H' },
			{ "cpol",    0, 0, 'O' },
			{ "lsb",     0, 0, 'L' },
			{ "cs-high", 0, 0, 'C' },
			{ "3wire",   0, 0, '3' },
			{ "no-cs",   0, 0, 'N' },
			{ "ready",   0, 0, 'R' },
			{ "dual",    0, 0, '2' },
			{ "verbose", 0, 0, 'v' },
			{ "quad",    0, 0, '4' },
			{ NULL, 0, 0, 0 },
		};
		int c;

		c = getopt_long(argc, argv, "D:s:d:b:i:o:lHOLC3NR24p:v",
				lopts, NULL);

		if (c == -1)
			break;

		switch (c) {
		case 'D':
			device = optarg;
			break;
		case 's':
			speed = atoi(optarg);
			break;
		case 'd':
			delay = atoi(optarg);
			break;
		case 'b':
			bits = atoi(optarg);
			break;
		case 'i':
			input_file = optarg;
			break;
		case 'o':
			output_file = optarg;
			break;
		case 'l':
			mode |= SPI_LOOP;
			break;
		case 'H':
			mode |= SPI_CPHA;
			break;
		case 'O':
			mode |= SPI_CPOL;
			break;
		case 'L':
			mode |= SPI_LSB_FIRST;
			break;
		case 'C':
			mode |= SPI_CS_HIGH;
			break;
		case '3':
			mode |= SPI_3WIRE;
			break;
		case 'N':
			mode |= SPI_NO_CS;
			break;
		case 'v':
			verbose = 1;
			break;
		case 'R':
			mode |= SPI_READY;
			break;
		case 'p':
			input_tx = optarg;
			break;
		case '2':
			mode |= SPI_TX_DUAL;
			break;
		case '4':
			mode |= SPI_TX_QUAD;
			break;
		default:
			print_usage(argv[0]);
			break;
		}
	}
	if (mode & SPI_LOOP) {
		if (mode & SPI_TX_DUAL)
			mode |= SPI_RX_DUAL;
		if (mode & SPI_TX_QUAD)
			mode |= SPI_RX_QUAD;
	}
}

static void transfer_escaped_string(int fd, char *str)
{
	size_t size = strlen(str);
	uint8_t *tx;
	uint8_t *rx;

	tx = malloc(size);
	if (!tx)
		pabort("can't allocate tx buffer");

	rx = malloc(size);
	if (!rx)
		pabort("can't allocate rx buffer");

	size = unescape((char *)tx, str, size);
	transfer(fd, tx, rx, size);
	free(rx);
	free(tx);
}

static void transfer_file(int fd, char *filename)
{
	ssize_t bytes;
	struct stat sb;
	int tx_fd;
	uint8_t *tx;
	uint8_t *rx;

	if (stat(filename, &sb) == -1)
		pabort("can't stat input file");

	tx_fd = open(filename, O_RDONLY);
	if (tx_fd < 0)
		pabort("can't open input file");

	tx = malloc(sb.st_size);
	if (!tx)
		pabort("can't allocate tx buffer");

	rx = malloc(sb.st_size);
	if (!rx)
		pabort("can't allocate rx buffer");

	bytes = read(tx_fd, tx, sb.st_size);
	if (bytes != sb.st_size)
		pabort("failed to read input file");

	transfer(fd, tx, rx, sb.st_size);
	free(rx);
	free(tx);
	close(tx_fd);
}


unsigned int int_to_bin(unsigned int k) {
	return (k == 0 || k == 1 ? k : ((k % 2) + 10 * int_to_bin(k / 2)));
}

void printRegisterName(int _address) {
	int TAB_WIDTH = 12;
    if(_address == ID){
        printf("%-*s (%#.2x)", TAB_WIDTH, "ID", _address);
    }
    else if(_address == CONFIG1){
        printf("%-*s (%#.2x)", TAB_WIDTH, "CONFIG1", _address);
    }
    else if(_address == CONFIG2){
        printf("%-*s (%#.2x)", TAB_WIDTH, "CONFIG2", _address);
    }
    else if(_address == CONFIG3){
        printf("%-*s (%#.2x)", TAB_WIDTH, "CONFIG3", _address);
    }
    else if(_address == LOFF){
        printf("%-*s (%#.2x)", TAB_WIDTH, "LOFF", _address);
    }
    else if(_address == CH1SET){
        printf("%-*s (%#.2x)", TAB_WIDTH, "CH1SET", _address);
    }
    else if(_address == CH2SET){
        printf("%-*s (%#.2x)", TAB_WIDTH, "CH2SET", _address);
    }
    else if(_address == CH3SET){
        printf("%-*s (%#.2x)", TAB_WIDTH, "CH3SET", _address);
    }
    else if(_address == CH4SET){
        printf("%-*s (%#.2x)", TAB_WIDTH, "CH4SET", _address);
    }
    else if(_address == CH5SET){
        printf("%-*s (%#.2x)", TAB_WIDTH, "CH5SET", _address);
    }
    else if(_address == CH6SET){
        printf("%-*s (%#.2x)", TAB_WIDTH, "CH6SET", _address);
    }
    else if(_address == CH7SET){
        printf("%-*s (%#.2x)", TAB_WIDTH, "CH7SET", _address);
    }
    else if(_address == CH8SET){
        printf("%-*s (%#.2x)", TAB_WIDTH, "CH8SET", _address);
    }
    else if(_address == BIASSENSP){
        printf("%-*s (%#.2x)", TAB_WIDTH, "BIAS_SENSP", _address);
    }
    else if(_address == BIASSENSN){
        printf("%-*s (%#.2x)", TAB_WIDTH, "BIAS_SENSN", _address);
    }
    else if(_address == LOFF_SENSP){
        printf("%-*s (%#.2x)", TAB_WIDTH, "LOFF_SENSP", _address);
    }
    else if(_address == LOFF_SENSN){
        printf("%-*s (%#.2x)", TAB_WIDTH, "LOFF_SENSN", _address);
    }
    else if(_address == LOFF_FLIP){
        printf("%-*s (%#.2x)", TAB_WIDTH, "LOFF_FLIP", _address);
    }
    else if(_address == LOFF_STATP){
        printf("%-*s (%#.2x)", TAB_WIDTH, "LOFF_STATP", _address);
    }
    else if(_address == LOFF_STATN){
        printf("%-*s (%#.2x)", TAB_WIDTH, "LOFF_STATN", _address);
    }
    else if(_address == GPIO){
        printf("%-*s (%#.2x)", TAB_WIDTH, "GPIO", _address);
    }
    else if(_address == PACE){
        printf("%-*s (%#.2x)", TAB_WIDTH, "MISC1", _address);
    }
    else if(_address == RESP){
        printf("%-*s (%#.2x)", TAB_WIDTH, "MISC2", _address);
    }
    else if(_address == CONFIG4){
        printf("%-*s (%#.2x)", TAB_WIDTH, "CONFIG4", _address);
    }
}

int main(int argc, char *argv[])
{
	int ret = 0;
	int fd;

	parse_opts(argc, argv);

	fd = open(device, O_RDWR);
	if (fd < 0)
		pabort("can't open device");

	/*
	 * spi mode
	 */
	ret = ioctl(fd, SPI_IOC_WR_MODE, &mode);
	if (ret == -1)
		pabort("can't set spi mode");

	ret = ioctl(fd, SPI_IOC_RD_MODE, &mode);
	if (ret == -1)
		pabort("can't get spi mode");

	/*
	 * bits per word
	 */
	ret = ioctl(fd, SPI_IOC_WR_BITS_PER_WORD, &bits);
	if (ret == -1)
		pabort("can't set bits per word");

	ret = ioctl(fd, SPI_IOC_RD_BITS_PER_WORD, &bits);
	if (ret == -1)
		pabort("can't get bits per word");

	/*
	 * max speed hz
	 */
	ret = ioctl(fd, SPI_IOC_WR_MAX_SPEED_HZ, &speed);
	if (ret == -1)
		pabort("can't set max speed hz");

	ret = ioctl(fd, SPI_IOC_RD_MAX_SPEED_HZ, &speed);
	if (ret == -1)
		pabort("can't get max speed hz");

	printf("spi mode: 0x%x\n", mode);
	printf("bits per word: %d\n", bits);
	printf("max speed: %d Hz (%d KHz)\n", speed, speed/1000);

	if (input_tx && input_file)
		pabort("only one of -p and --input may be selected");

//	if (input_tx)
//		transfer_escaped_string(fd, input_tx);
//	else if (input_file)
//		transfer_file(fd, input_file);
//	else
//		transfer(fd, default_tx, default_rx, sizeof(default_tx));

	// reset chip
	printf("Reset chip...!\n");
	uint8_t tx0[] = { SPI_RESET };
	transfer(fd, tx0, default_rx, sizeof(tx0));


	// read ID
	uint8_t RREG = 0x20;
	uint8_t reg = 0x00;
	uint8_t regStartAddr = 0x00;
	uint8_t regEndAddr = 0x17;
	int out;
	uint8_t tx_read_id[] = {
		RREG | reg, 0x00, 0x00 };

	transfer(fd, tx_read_id, default_rx, sizeof(tx_read_id));

	printf("Reading register 0x00 to 0x17...\n");
	// read all registers 0x00 - 0x17
	uint8_t tx1[] = { RREG | regStartAddr };
	transfer(fd, tx1, default_rx, sizeof(tx1)); // reg start
	uint8_t tx2[] = { regEndAddr };
	transfer(fd, tx2, default_rx, sizeof(tx2)); // reg end
	int i;
	uint8_t tx3[] = { 0x00 };
	for (i = 0 ; i <= regEndAddr ; i++) {
		printRegisterName(i);
		printf("\n");
		transfer(fd, tx3, default_rx, sizeof(tx3));
//		printRegisterName(i);
//		printf("R: %d (%#02x)\n", int_to_bin(out), out);

	}
//
//	// read all registers
//	void adc_rregs(int spi_cs, int regStartAddr, int regEndAddr) {
//		mraa_gpio_context _gpio_cs;
//		switch (spi_cs) { case 0: _gpio_cs = gpio_IPIN_CS; break; case 1: _gpio_cs = gpio_IPIN_CS2; break; }
//		printf("--------------------------------\n");
//		int out = 0;
//		mraa_gpio_write(_gpio_cs, 0);
//		mraa_spi_write(spi, RREG | regStartAddr); //opcode1
//		mraa_spi_write(spi, regEndAddr); //opcode2
//
//		int i;
//
//		for (i = 0; i <= regEndAddr ; i++) {
//			out = mraa_spi_write(spi, 0);
//			if (app_conf.verbose) {
//				printRegisterName(i);
//				printf("R: %d (%#02x)\n", int_to_bin(out), out);
//			}
//		}
//
//		mraa_gpio_write(_gpio_cs, 1);
//		printf("--------------------------------\n");
//
//
//	}



	close(fd);

	return ret;
}



//
//
//
// int main() {
////	 int adc_rreg(int spi_cs, int reg) {
//
//
//
////	mraa_gpio_context _gpio_cs;
////	switch (spi_cs) { case 0: _gpio_cs = gpio_IPIN_CS; break; case 1: _gpio_cs = gpio_IPIN_CS2; break; }
//
//	int RREG = 0x20;
//	int reg = 0x00;
//	int out = 0;
////	mraa_gpio_write(_gpio_cs, 0);
//	mraa_spi_write(spi, RREG | reg);
//	mraa_spi_write(spi, 0);
//	out = mraa_spi_write(spi, 0);
//
//
//
////	if (app_conf.verbose)
////		printf("R: %d (%#02x)\n", int_to_bin(out), out);
////	mraa_gpio_write(_gpio_cs, 1);
//	return out;
////	 }
// }
//
// int main(int argc, char** argv) {
//
//	init_app_default_config(&app_conf);
//
//	memset(&ads1299_prog_conf, 0, sizeof(ads1299_prog_conf_t));
//	init_ads1299_default_prog_conf(&ads1299_prog_conf);
//
//
//	// structure to store ADS1299 data, e.g. timestamp, channel raw, lead off detection, photosensor state
//	memset(&adsdata, 0, sizeof(adsdata_t));
//	memset(&adsdata2, 0, sizeof(adsdata_t));
//
//	memset(&mpu_dev_conf, 0, sizeof(mpu9250_dev_conf_t));
//
////	util_setup_sig_catcher(&sig_catch_handler);
//
//	print_info("Parsing user arguments...\n");
////	if (parse_args(argc, argv, &app_conf, &ads1299_prog_conf)) { usage(); exit(1); } // exit the program if args parsing failed
//	struct arguments arguments;
//
//	/* Parse our arguments; every option seen by `parse_opt' will
//	 be reflected in `arguments'. */
//	if ( argp_parse (&argp, argc, argv, 0, 0, &arguments) != 0 ) {
//		exit(1);
//	}
//
//	if (app_conf.is_ads1299_sensor_enable) {
//		printf("******************************************\n");
//		print_info("Initializing ADS1299 chip #1 on SPI CS0 (Sending SDATAC SPI command)...\n");
//		if (init_ads1299_chip(ADS1299_BOARD_1, &ads1299_prog_conf)) { print_error("ADS1299 Chip #1 Initialization...\t" RED "failed" RESET "\n"); exit(1); } print_info("ADS1299 Chip Initialization...\t" GRN "ok" RESET "\n");
//
//		if (app_conf.verbose) {
//			printf("Reading ADS1299 on CS0...\n");
//			printf("Reading ID register...\n");
//			printf("Device ID: %s\n", getDeviceId(ADS1299_BOARD_1));
//
//			printf("Supported Channels: %d\n", getTotalNumOfChannels(ADS1299_BOARD_1));
//
//			adc_rregs(ADS1299_BOARD_1, 0x00, 0x17); // read all registers starting from ID (0x00) to CONFIG4 (0x17)
//
//			// test write
////			printf("Testing writing 0xE0 to CONFIG3...\n");
////			adc_wreg(ADS1299_BOARD_1, CONFIG3, 0xE0);
////			if (adc_rreg(ADS1299_BOARD_1, CONFIG3) == 0xE0)
////				printf("OK!\n");
////			else
////				printf("Failed!\n");
//		}
//	}
//
//
// }



// EOF


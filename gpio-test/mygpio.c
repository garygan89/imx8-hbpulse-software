#include <gpiod.h>

struct gpiod_chip *chip;
struct gpiod_line *line;
int rv, value;

int main() {
chip = gpiod_chip_open_by_name("gpiochip4");
if (!chip)
	return -1;


line = gpiod_chip_get_line(chip, 10);
if (!line) {
	gpiod_chip_close(chip);
	return -1;
}
gpiod_line_request_output(line, "foo", 0);
gpiod_chip_close(chip);
}

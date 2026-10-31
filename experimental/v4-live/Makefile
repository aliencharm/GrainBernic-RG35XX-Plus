CC ?= cc
CPPFLAGS ?=
CFLAGS ?= -O2 -std=c11 -Wall -Wextra -Werror
BUILD ?= build
.PHONY: all test clean
all: $(BUILD)/v4-live
$(BUILD):
	mkdir -p $@
$(BUILD)/v4-live: src/audio.c src/dsp.c src/dsp.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) src/audio.c src/dsp.c -o $@ -lm -ldl
$(BUILD)/test-dsp: tests/test_dsp.c src/dsp.c src/dsp.h | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) -Isrc tests/test_dsp.c src/dsp.c -o $@ -lm
test: $(BUILD)/test-dsp
	$(BUILD)/test-dsp
clean:
	rm -rf $(BUILD)

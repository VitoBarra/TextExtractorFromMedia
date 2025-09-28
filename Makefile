APP_NAME = MediaTranscriber
SRC      = main.py
VERSION  ?= 1.0.0
MODE     ?= release

OS := $(shell uname -s)

ifeq ($(OS),Windows_NT)
    TARGET = dist/$(APP_NAME).exe
else
    TARGET = dist/$(APP_NAME)
endif

PYI_OPTS = --onefile --clean --noconfirm

ifeq ($(MODE),release)
    PYI_OPTS += --strip --noconsole
else
    PYI_OPTS += --debug=all
endif

.PHONY: all build clean run install check package

all: build

check:
	@command -v pyinstaller >/dev/null 2>&1 || { echo "PyInstaller not installed. Run: pip install pyinstaller"; exit 1; }

build: check
	@if [ -f "$(TARGET)" ]; then \
		echo ">>> $(TARGET) already exists. Skipping build."; \
	else \
		echo ">>> Building $(APP_NAME) ($(MODE)) v$(VERSION)..."; \
		pyinstaller $(PYI_OPTS) --name $(APP_NAME) $(SRC); \
	fi

run: build
	@echo ">>> Running $(APP_NAME)..."
	./$(TARGET)

clean:
	@echo ">>> Cleaning executable..."
	@if [ -f "$(TARGET)" ]; then \
		rm -f "$(TARGET)"; \
		echo ">>> $(TARGET) removed."; \
	else \
		echo ">>> No executable found to remove."; \
	fi


install: build
	@echo ">>> Installing $(APP_NAME) to /usr/local/bin..."
	sudo cp $(TARGET) /usr/local/bin/$(APP_NAME)

package: build
	tar -czvf $(APP_NAME)-$(VERSION).tar.gz -C dist $(notdir $(TARGET))

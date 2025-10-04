APP_NAME = MediaTranscriber
SRC      = main.py
VERSION  ?= 1.0.0
MODE     ?= release

DOCKER_FOLDER = DockerDeploy
EXPORT_FOLDER = Bundles

PYI_OPTS = --onefile --clean --noconfirm
ifeq ($(MODE),release)
    PYI_OPTS += --strip --noconsole
else
    PYI_OPTS += --debug=all
endif

.PHONY: all build clean package docker_x86 docker_arm docker_win check prepare

all: build

# Ensure Docker is installed
check:
	@command -v docker >/dev/null 2>&1 || { echo "Docker not installed. Install Docker first."; exit 1; }

# Ensure deploy folder exists
prepare:
	@mkdir -p $(EXPORT_FOLDER)

# Build all targets via Docker
build: prepare docker_x86 docker_arm docker_win
	@echo ">>> All builds complete."

# Docker build for Linux x86_64
docker_x86: check prepare
ifeq ("$(wildcard $(EXPORT_FOLDER)/$(APP_NAME)-x86_64)","")
	@echo ">>> Building $(APP_NAME) for Linux x86_64..."
	docker build -f $(DOCKER_FOLDER)/Dockerfile.linux.x86_64 -t media-x86_64 .
	docker run --rm -v $(PWD)/$(EXPORT_FOLDER):/src/deploy media-x86_64
	@echo ">>> Linux x86_64 build finished."
else
	@echo ">>> Linux x86_64 binary already exists. Skipping build."
endif

# Docker build for Linux aarch64 (ARM64)
docker_arm: check prepare
ifeq ("$(wildcard $(EXPORT_FOLDER)/$(APP_NAME)-aarch64)","")
	@echo ">>> Building $(APP_NAME) for Linux aarch64 (ARM64)..."
	# Create and use a buildx builder (if it doesn't exist)
	-@docker buildx inspect builder-arm64 >/dev/null 2>&1 || docker buildx create --name builder-arm64 --use
	docker buildx use builder-arm64
	# Register QEMU for cross-platform emulation (if not already registered)
	-@docker run --rm --privileged multiarch/qemu-user-static --reset -p yes || true
	# Build the ARM64 image
	docker buildx build --platform linux/arm64 \
		-f $(DOCKER_FOLDER)/Dockerfile.linux.aarch64 \
		-t media-arm64 \
		--load .
	# Run the ARM64 container (with emulation via QEMU)
	docker run --rm -v $(PWD)/$(EXPORT_FOLDER):/src/deploy media-arm64
	@echo ">>> Linux aarch64 build finished."
else
	@echo ">>> Linux aarch64 binary already exists. Skipping build."
endif


# Docker build for Windows (x86_64) using Wine
docker_win: check prepare
ifeq ("$(wildcard $(EXPORT_FOLDER)/$(APP_NAME).exe)","")
	@echo ">>> Building $(APP_NAME) for Windows..."
	docker build -f $(DOCKER_FOLDER)/Dockerfile.windows -t media-win .
	docker run --rm -v $(PWD)/$(EXPORT_FOLDER):/src/deploy media-win
	@echo ">>> Windows build finished."
else
	@echo ">>> Windows binary already exists. Skipping build."
endif

# Clean build artifacts
clean:
	@echo ">>> Cleaning deploy folder..."
	rm -rf $(EXPORT_FOLDER)/$(APP_NAME)-* $(EXPORT_FOLDER)/$(APP_NAME).exe
	rm -rf $(EXPORT_FOLDER)/build $(EXPORT_FOLDER)/*.spec
	@echo ">>> Clean complete."

# Package all builds into tar.gz files
package: build
	@echo ">>> Packaging binaries..."
ifeq ("$(wildcard $(EXPORT_FOLDER)/$(APP_NAME)-x86_64)","")
	@echo ">>> Skipping x86_64 package, binary missing."
else
	tar -czvf $(EXPORT_FOLDER)/$(APP_NAME)-$(VERSION)-x86_64.tar.gz -C $(EXPORT_FOLDER) $(APP_NAME)-x86_64
endif

ifeq ("$(wildcard $(EXPORT_FOLDER)/$(APP_NAME)-aarch64)","")
	@echo ">>> Skipping aarch64 package, binary missing."
else
	tar -czvf $(EXPORT_FOLDER)/$(APP_NAME)-$(VERSION)-aarch64.tar.gz -C $(EXPORT_FOLDER) $(APP_NAME)-aarch64
endif

ifeq ("$(wildcard $(EXPORT_FOLDER)/$(APP_NAME).exe)","")
	@echo ">>> Skipping Windows package, binary missing."
else
	tar -czvf $(EXPORT_FOLDER)/$(APP_NAME)-$(VERSION)-win.tar.gz -C $(EXPORT_FOLDER) $(APP_NAME).exe
endif
	@echo ">>> Packaging complete."

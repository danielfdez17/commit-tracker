# Shared configuration.
# Values assigned with ?= can be overridden from the command line, or from
# the root Makefile before this file is included.

SHELL := /usr/bin/bash
.SHELLFLAGS := -ec

GREEN := $(shell printf '\033[0;32m')
YELLOW := $(shell printf '\033[0;33m')
RESET := $(shell printf '\033[0m')
CYAN := $(shell printf '\033[0;36m')
ORANGE := $(shell printf '\033[0;31m')
RED := $(shell printf '\033[0;31m')
SUCCESS := $(GREEN)✓
FAIL := $(RED)✗
INFO := $(CYAN)ℹ
WARN := $(YELLOW)⚠

PRINT_BANNER ?= ./scripts/bash/print_banner.sh
PRINT_SUCCESS ?= ./scripts/bash/print_success.sh
PRINT_FAIL ?= ./scripts/bash/print_fail.sh
PRINT_INFO ?= ./scripts/bash/print_info.sh
PRINT_WARN ?= ./scripts/bash/print_warning.sh

RUN_AND_LOG ?= ./scripts/bash/run_and_log.sh

COMPOSE ?= docker compose

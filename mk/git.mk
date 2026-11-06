# ── Git

.PHONY: update-submodules
update-submodules: ## Update git submodules
	@$(PRINT_BANNER) "Updating Git Submodules"
	@git submodule update --init --recursive --remote
	@$(PRINT_SUCCESS) "Git submodules updated successfully!"

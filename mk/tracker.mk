# ── Tracker

GH_LOGIN ?=

.PHONY: contributions streak longest-streak
contributions: ## Total GitHub contributions (last year and all time)
	@$(PRINT_BANNER) "Total contributions"
	@python3 -m tracker contributions $(if $(GH_LOGIN),--login $(GH_LOGIN),)

streak: ## Current GitHub contribution streak
	@$(PRINT_BANNER) "Current streak"
	@python3 -m tracker streak $(if $(GH_LOGIN),--login $(GH_LOGIN),)

longest-streak: ## Longest GitHub contribution streak
	@$(PRINT_BANNER) "Longest streak"
	@python3 -m tracker longest-streak $(if $(GH_LOGIN),--login $(GH_LOGIN),)

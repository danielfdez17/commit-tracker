# ── Tracker

GH_LOGIN ?=

.PHONY: contributions
contributions: ## Total GitHub contributions (last year and all time)
	@$(PRINT_BANNER) "Total contributions"
	@python3 -m tracker contributions $(if $(GH_LOGIN),--login $(GH_LOGIN),)

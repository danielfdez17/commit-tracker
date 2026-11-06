# ── Tracker

GH_LOGIN ?=

.PHONY: contributions streak longest-streak languages commits pull-requests issues weekly-commits yearly-contributions public-repositories
contributions: ## Total GitHub contributions (last year and all time)
	@$(PRINT_BANNER) "Total contributions"
	@python3 -m tracker contributions $(if $(GH_LOGIN),--login $(GH_LOGIN),)

streak: ## Current GitHub contribution streak
	@$(PRINT_BANNER) "Current streak"
	@python3 -m tracker streak $(if $(GH_LOGIN),--login $(GH_LOGIN),)

longest-streak: ## Longest GitHub contribution streak
	@$(PRINT_BANNER) "Longest streak"
	@python3 -m tracker longest-streak $(if $(GH_LOGIN),--login $(GH_LOGIN),)

languages: ## Top GitHub languages by code size
	@$(PRINT_BANNER) "Top languages"
	@python3 -m tracker languages $(if $(GH_LOGIN),--login $(GH_LOGIN),)

commits: ## Total GitHub contribution commits (last year and all time)
	@$(PRINT_BANNER) "Total commits"
	@python3 -m tracker commits $(if $(GH_LOGIN),--login $(GH_LOGIN),)

pull-requests: ## Pull requests opened on GitHub
	@$(PRINT_BANNER) "Pull requests"
	@python3 -m tracker pull-requests $(if $(GH_LOGIN),--login $(GH_LOGIN),)

issues: ## Issues opened on GitHub
	@$(PRINT_BANNER) "Issues opened"
	@python3 -m tracker issues $(if $(GH_LOGIN),--login $(GH_LOGIN),)

weekly-commits: ## Contribution commits per week
	@$(PRINT_BANNER) "Commits per week"
	@python3 -m tracker weekly-commits $(if $(GH_LOGIN),--login $(GH_LOGIN),)

yearly-contributions: ## GitHub contributions per calendar year
	@$(PRINT_BANNER) "Contributions per year"
	@python3 -m tracker yearly-contributions $(if $(GH_LOGIN),--login $(GH_LOGIN),)

public-repositories: ## Public GitHub repositories owned by the user
	@$(PRINT_BANNER) "Public repositories"
	@python3 -m tracker public-repositories $(if $(GH_LOGIN),--login $(GH_LOGIN),)

# ── Utils

.PHONY: help
help: ## Show available targets
	@$(PRINT_BANNER) "Available Makefile Targets"
	@LC_ALL=C.UTF-8 awk '\
		function trim(s) { \
			sub(/^[[:space:]]+/, "", s); \
			sub(/[[:space:]]+$$/, "", s); \
			return s \
		} \
		/^# ──[[:space:]]+/ { \
			title = $$0; \
			sub(/^# ──[[:space:]]+/, "", title); \
			sub(/[[:space:]]*─+[[:space:]]*$$/, "", title); \
			title = trim(title); \
			n++; kind[n] = "section"; text[n] = title; \
			next \
		} \
		/^[a-zA-Z_-]+:.*## / { \
			name = $$0; sub(/:.*/, "", name); \
			msg = $$0; sub(/^[^#]*## /, "", msg); \
			n++; kind[n] = "target"; names[n] = name; msgs[n] = msg; \
			if (length(name) > name_width) name_width = length(name); \
			next \
		} \
		END { \
			for (i = 1; i <= n; i++) \
				if (kind[i] == "target") { \
					line = 2 + name_width + 1 + length(msgs[i]); \
					if (line > line_width) line_width = line \
				} \
			for (i = 1; i <= n; i++) \
				if (kind[i] == "section") { \
					label = "── " text[i] " "; \
					pad = line_width - length(label); \
					if (pad < 1) pad = 1; \
					dashes = ""; \
					for (j = 0; j < pad; j++) dashes = dashes "─"; \
					printf "%s%s\n", label, dashes \
				} else \
					printf "  $(CYAN)%-*s$(RESET) %s\n", name_width, names[i], msgs[i] \
		}' $(MAKEFILE_LIST)

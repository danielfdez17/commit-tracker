# Entry point. Set the default goal before including modules so a target
# defined in mk/*.mk cannot become the default.
#
# Add a module by creating mk/<name>.mk and appending an include below.
.DEFAULT_GOAL := help

include mk/config.mk
include mk/help.mk
include mk/git.mk
include mk/tracker.mk

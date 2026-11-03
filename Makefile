# BRANCH is a kodi-addon-checker version name: matrix, nexus, or omega.
BRANCH ?= matrix
ADDON_ID := plugin.video.crossfitwod

.PHONY: validate
validate:
	@tmpdir=$$(mktemp -d); \
	ln -s "$$(pwd)" "$$tmpdir/$(ADDON_ID)"; \
	kodi-addon-checker --branch $(BRANCH) "$$tmpdir/$(ADDON_ID)"; \
	status=$$?; \
	rm -rf "$$tmpdir"; \
	exit $$status

.DEFAULT_GOAL := all
.PHONY: all download-inputs deploy-release
TODAY ?=$(shell date +%Y-%m-%d)
VERSION=v$(TODAY)


# MAIN COMMANDS / GOALS ------------------------------------------------------------------------------------------------
all: output/release/gard.owl deploy-release

output/release/gard.owl output/release/gard.sssom.tsv output/release/gard-mondo.sssom.tsv output/release/gard-mondo-exact.sssom.tsv output/release/gard-mondo-exact_curation.sssom.tsv gard-mondo_curation.sssom.tsv: | output/release/
	 python3 -m gard_owl_ingest

# Analysis
output/analysis/gard-mondo.sssom-like-exact.tsv output/analysis/gard-mondo.sssom-like.tsv output/analysis/gard_terms_mapping_status-exact.csv output/analysis/gard_terms_mapping_status.csv output/analysis/gard_unmapped_terms-exact.txt output/analysis/gard_unmapped_terms.txt output/analysis/obsoleted_gard_terms_in_mondo.txt: tmp/input/mondo.sssom.tsv
	python3 gard_owl_ingest/mondo_mapping_status.py

# Utils
output/:
	mkdir -p $@

output/release/: | output/
	mkdir -p $@

tmp/input/:
	mkdir -p $@

tmp/input/mondo.sssom.tsv: tmp/input/
	wget http://purl.obolibrary.org/obo/mondo/mappings/mondo.sssom.tsv -O $@

tmp/input/mondo_hasdbxref_gard.sssom.tsv: tmp/input/
	wget http://purl.obolibrary.org/obo/mondo/mappings/mondo_hasdbxref_gard.sssom.tsv -O $@

download-inputs: tmp/input/mondo.sssom.tsv tmp/input/mondo_hasdbxref_gard.sssom.tsv

deploy-release: | output/release/
	@test $(VERSION)
	gh release create $(VERSION) --notes "New release." --title "$(VERSION)" output/release/*

# SETUP / INSTALLATION -------------------------------------------------------------------------------------------------
install:
	pip install -r requirements.txt

# HELP -----------------------------------------------------------------------------------------------------------------
help:
	@echo "-----------------------------------"
	@echo "	Command reference: GARD OWL Ingest"
	@echo "-----------------------------------"
	@echo "all"
	@echo "Creates all release artefacts.\n"
	@echo "gard.owl"
	@echo "Creates OWL artefact: gard.owl\n"
	@echo "install"
	@echo "Install's Python requirements.\n"

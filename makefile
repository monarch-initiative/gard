.PHONY: all


# MAIN COMMANDS / GOALS ------------------------------------------------------------------------------------------------
all: gard.db

# TODO: Dockerized SemSQL I think is best way to do this
gard.db: gard.owl
	echo TODO

gard.owl:
	 python3 -m gard_owl_ingest

# Analysis
tmp/gard_terms_mapping_status.tsv tmp/obsoleted_gard_terms_in_mondo.tsv tmp/gard_unmapped_terms.txt: tmp/mondo.sssom.tsv
	python3 gard_owl_ingest/analysis/mondo_mapping_status.py

# Utils
tmp/:
	mkdir -p $@

tmp/input/mondo.sssom.tsv: tmp/
	wget http://purl.obolibrary.org/obo/mondo/mappings/mondo.sssom.tsv -O $@

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
	@echo "gard.db"
	@echo "Creates SemanticSQL sqlite artefact: gard.db\n"
	@echo "install"
	@echo "Install's Python requirements.\n"

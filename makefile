.PHONY: all


# MAIN COMMANDS / GOALS ------------------------------------------------------------------------------------------------
all: gard.db

# TODO: Dockerized SemSQL I think is best way to do this
gard.db: gard.owl
	echo TODO

gard.owl:
	 python3 -m gard_owl_ingest

# Analysis
tmp/gard-terms-mapping-status.tsv tmp/obsoleted-gard-terms-in-mondo.tsv: tmp/mondo.sssom.tsv
	python3 gard_owl_ingest/analysis/mondo_mapping_status.py

# Utils
tmp/:
	mkdir -p tmp

tmp/mondo.sssom.tsv: tmp/
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

"""Configuration for GARD OWL Ingest."""
import os
from pathlib import Path
from typing import List

# Types
CURIE = str
MAPPING_PREDICATE = str
# Paths: directories
SRC_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = SRC_DIR.parent
DATA_DIR = PROJECT_DIR / 'data'
TMP_DIR = PROJECT_DIR / 'tmp'
TMP_INPUT_DIR = TMP_DIR / 'input'
OUTPUT_DIR = PROJECT_DIR / 'output'
RELEASE_DIR = OUTPUT_DIR / 'release'
ANALYSIS_OUTDIR = OUTPUT_DIR / 'analysis'
# Paths: files
# ROBOT_PATH = 'robot'  # 2023/04/19: Strangely, this worked. Then, an hour later, only /usr/local/bin/robot worked
ROBOT_PATH = '/usr/local/bin/robot'
OUTPATH_OWL = RELEASE_DIR / 'gard.owl'
OUTPATH_SSSOM = RELEASE_DIR / 'gard.sssom.tsv'
SSSOM_METADATA_PATH = DATA_DIR / 'gard.sssom-metadata.yml'
MONDO_SSSOM_METADATA_PATH = DATA_DIR / 'gard-mondo.sssom-metadata.yml'
DATASOURCE_CSV = DATA_DIR / 'GARD_disease_list.csv'
OUTPATH_ROBOT_TEMPLATE = TMP_DIR / 'gard.robot.template.tsv'
MONDO_SSSOM_TSV = TMP_INPUT_DIR / 'mondo.sssom.tsv'
GARD_MONDO_OLD_SSSOM_TSV = TMP_INPUT_DIR / 'mondo_hasdbxref_gard.sssom.tsv'
# IRIs, IRI Prefixes, CURIEs
GARD_ONTOLOGY_IRI = 'http://purl.obolibrary.org/obo/GARD/ontology'
GARD_PURL = 'http://purl.obolibrary.org/obo/GARD_'
GARD_PREFIX_MAP_STR = f'GARD: {GARD_PURL}'
ORDO_PREFIX_MAP_STR = f'Orphanet: http://www.orpha.net/ORDO/Orphanet_'
OMIM_PREFIX_MAP_STR = f'OMIM: https://omim.org/entry/'
OMIMPS_PREFIX_MAP_STR = f'OMIMPS: https://omim.org/phenotypicSeries/PS'
MAPPING_PREDICATES: List[MAPPING_PREDICATE] = [
    'skos:exactMatch', 'skos:narrowMatch', 'skos:broadMatch', 'skos:relatedMatch']

# Create directories if they don't exist
for _dir in [OUTPUT_DIR, RELEASE_DIR, ANALYSIS_OUTDIR, TMP_DIR, TMP_INPUT_DIR]:
    if not os.path.exists(_dir):
        os.makedirs(_dir)

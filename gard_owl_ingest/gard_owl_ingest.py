"""GARD to OWL"""
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd

sys.path.insert(0, os.getcwd())
from gard_owl_ingest.analysis.mondo_mapping_status import MAPPING_PREDICATES, gard_native_mappings

CURIE = str
MAPPING_PREDICATE = str
SRC_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = SRC_DIR.parent
DATA_DIR = PROJECT_DIR / 'data'
TMP_DIR = PROJECT_DIR / 'tmp'
RELEASE_DIR = PROJECT_DIR / 'release'
DATASOURCE_CSV = DATA_DIR / 'GARD_disease_list.csv'
OUTPATH_ROBOT_TEMPLATE = TMP_DIR / 'gard.robot.template.tsv'
OUTPATH_OWL = RELEASE_DIR / 'gard.owl'
OUTPATH_SSSOM = RELEASE_DIR / 'gard.sssom.tsv'
# ROBOT_PATH = 'robot'  # 2023/04/19: Strangely, this worked. Then, an hour later, only /usr/local/bin/robot worked
ROBOT_PATH = '/usr/local/bin/robot'
SSSOM_METADATA_PATH = DATA_DIR / 'sssom-metadata.yml'
GARD_ONTOLOGY_IRI = 'http://purl.obolibrary.org/obo/GARD/ontology'
GARD_PURL = 'http://purl.obolibrary.org/obo/GARD_'
GARD_PREFIX_MAP_STR = f'GARD: {GARD_PURL}'
ORDO_PREFIX_MAP_STR = f'Orphanet: http://www.orpha.net/ORDO/Orphanet_'
OMIM_PREFIX_MAP_STR = f'OMIM: https://omim.org/entry/'
OMIMPS_PREFIX_MAP_STR = f'OMIMPS: https://omim.org/phenotypicSeries/PS'

# TODO: Create SSSOM at the end of this
# todo: later: split up OWL and SSSOM into different funcs
def run_ingest(outpath_owl: str = OUTPATH_OWL, outpath_sssom: str = OUTPATH_SSSOM):
    """Run the ingest"""
    src_df = pd.read_csv(DATASOURCE_CSV).fillna('')
    mappings: Dict[CURIE: Dict[MAPPING_PREDICATE, List[CURIE]]] = gard_native_mappings()

    # Convert Pandas DataFrame tuple row representation to robot style row.
    d: Dict[CURIE, Dict[str, str]] = {}
    for row in src_df.itertuples():
        # noinspection PyUnresolvedReferences Note_becausePycharmDoesntKnowAboutNamedTuples
        id_gard = row.GardID
        curie_gard = f'GARD:{id_gard}'
        # noinspection PyUnresolvedReferences Note_becausePycharmDoesntKnowAboutNamedTuples
        d_row = {
            'ID': curie_gard,
            'Label': row.SourceName,
            'Type': 'class',
            'Parent Class': '|'.join([f'GARD:{str(x)}' for x in row.ParentGardID[1:-1].split(', ')])
            if row.ParentGardID else '',
        }
        # Add mappings as w/ objects as string litral CURIEs
        for pred, obj_list in mappings[curie_gard].items():
            d_row[pred] = '|'.join(obj_list)
        d[curie_gard] = d_row

    # SSSOM
    # - generate dataframe
    sssom_rows: List[Dict] = []
    for row in src_df.itertuples():
        # noinspection PyUnresolvedReferences Note_becausePycharmDoesntKnowAboutNamedTuples
        id_gard = row.GardID
        curie_gard = f'GARD:{id_gard}'
        for pred, obj_list in mappings[curie_gard].items():
            for obj in obj_list:
                # noinspection PyUnresolvedReferences Note_becausePycharmDoesntKnowAboutNamedTuples
                category: str = '|'.join(row.DisorderType[1:-1].split(', '))
                # noinspection PyUnresolvedReferences Note_becausePycharmDoesntKnowAboutNamedTuples
                d_row = {
                    'subject_id': curie_gard,
                    'subject_label': row.SourceName,  # I think this is right; GARD doesn't change source label
                    'predicate_id': pred,
                    'object_id': obj,
                    'object_label': row.SourceName,
                    'subject_category': category,
                    'object_category': category,  # todo: I think correct category same, but if narrow/broad, not 100% sure
                    'object_source': row.DataSource,
                    'mapping_justification': 'semapv:ManualMappingCuration',
                }
                sssom_rows.append(d_row)
    sssom_df = pd.DataFrame(sssom_rows)
    # - write metadata
    f = open(SSSOM_METADATA_PATH, "r")
    lines = f.readlines()
    f.close()
    output_lines = []
    for line in lines:
        output_lines.append("# " + line)
    metadata_str = ''.join(output_lines)
    if os.path.exists(outpath_sssom):
        os.remove(outpath_sssom)
    f = open(outpath_sssom, 'a')
    f.write(metadata_str)
    f.close()
    # write data
    sssom_df.to_csv(outpath_sssom, index=False, sep='\t', mode='a')

    # OWL
    # - Convert to robot.template (http://robot.obolibrary.org/template)
    robot_subheader = {'ID': 'ID', 'Label': 'A rdfs:label', 'Type': 'TYPE', 'Parent Class': 'SC % SPLIT=|'} | \
                      {p: f'AI {p} SPLIT=|' for p in MAPPING_PREDICATES}
    robot_rows = [robot_subheader] + list(d.values())
    robot_df = pd.DataFrame(robot_rows)
    robot_df.to_csv(OUTPATH_ROBOT_TEMPLATE, index=False, sep='\t')

    # - Convert to OWL
    command = f'export ROBOT_JAVA_ARGS=-Xmx28G; ' \
              f'"{ROBOT_PATH}" template ' \
              f'--template "{OUTPATH_ROBOT_TEMPLATE}" ' \
              f'--prefix "{GARD_PREFIX_MAP_STR}" ' \
              f'--prefix "{ORDO_PREFIX_MAP_STR}" '\
              f'--prefix "{OMIM_PREFIX_MAP_STR}" ' \
              f'--prefix "{OMIMPS_PREFIX_MAP_STR}" ' \
              f'--ontology-iri "{GARD_ONTOLOGY_IRI}" ' \
              f'--output "{outpath_owl}"'
    results = subprocess.run(command, capture_output=True, shell=True)
    print(results.stdout.decode())

    return


if __name__ == '__main__':
    run_ingest()

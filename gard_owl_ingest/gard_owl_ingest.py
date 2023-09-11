"""GARD to OWL

Mapping outputs going online here:
https://drive.google.com/drive/folders/1jnBRzJNyShbf3vSq5ypvJYrVBiRr7iCb
"""
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd

THIS_DIR = Path(os.path.dirname(__file__))
PROJECT_ROOT = THIS_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
from gard_owl_ingest.config import CURIE, DATASOURCE_CSV, GARD_ONTOLOGY_IRI, GARD_PREFIX_MAP_STR, MAPPING_PREDICATE, \
    MAPPING_PREDICATES, OMIMPS_PREFIX_MAP_STR, OMIM_PREFIX_MAP_STR, ORDO_PREFIX_MAP_STR, OUTPATH_OWL, \
    OUTPATH_ROBOT_TEMPLATE, OUTPATH_SSSOM, ROBOT_PATH, SSSOM_METADATA_PATH
from gard_owl_ingest.mondo_mapping_status import gard_mondo_mapping_status, get_gard_native_mappings
from gard_owl_ingest.utils import write_tsv_with_comments


# todo: later: split up OWL and SSSOM into different funcs
def run_ingest(outpath_owl: str = OUTPATH_OWL, outpath_sssom: str = OUTPATH_SSSOM):
    """Run the ingest"""
    # Set up
    src_df = pd.read_csv(DATASOURCE_CSV).fillna('')
    mappings: Dict[CURIE: Dict[MAPPING_PREDICATE, List[CURIE]]] = get_gard_native_mappings()

    # - convert Pandas DataFrame tuple row representation to robot style row.
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

    # gard.sssom.tsv
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
    write_tsv_with_comments(sssom_df, SSSOM_METADATA_PATH, outpath_sssom)

    # output/analysis/ and some output/release/
    # todo: refactor: it's kinda wonky that some things in this function get output into release
    gard_mondo_mapping_status()  # all mappings for Mondo::proxy and GARD::proxy
    gard_mondo_mapping_status(mondo_predicate_filter=['skos:exactMatch'], gard_predicate_filter=['skos:exactMatch'])

    # gard.owl
    # - convert to robot.template (http://robot.obolibrary.org/template)
    robot_subheader = {'ID': 'ID', 'Label': 'A rdfs:label', 'Type': 'TYPE', 'Parent Class': 'SC % SPLIT=|'} | \
                      {p: f'AI {p} SPLIT=|' for p in MAPPING_PREDICATES}
    robot_rows = [robot_subheader] + list(d.values())
    robot_df = pd.DataFrame(robot_rows)
    robot_df.to_csv(OUTPATH_ROBOT_TEMPLATE, index=False, sep='\t')

    # - convert to OWL
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

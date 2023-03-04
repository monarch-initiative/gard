"""GARD to OWL"""
import os
from pathlib import Path
from typing import Dict

import pandas as pd

CURIE = str
SRC_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = SRC_DIR.parent
DATA_DIR = PROJECT_DIR / 'data'
DATASOURCE_CSV = DATA_DIR / 'GARD_disease_list.csv'


def run_ingest():
    """Run the ingest"""
    # temp: header
    # GardID,DataSource,SourceID,ClassificationLevel,DisorderType,SourceName,SourceSynonym,SourceDescription,OmimMember,
    # ParentOrphaCode,ParentOrphaName,ParentGardID,RdRequestID
    src_df = pd.read_csv(DATASOURCE_CSV)

    d: Dict[CURIE, Dict[str, str]] = {}
    for _, row in src_df.iterrows():
        # todo: ignore some concept_class_ids?
        id_gard = row['GardID']
        id_src = row['SourceID']
        label = row['SourceName']
        src_onto_name = row['DataSource']
        prefix = src_onto_name  # TODO: from using vocab_name and looking up a prefix_map
        curie_gard = f'GARD:{id_gard}'  # todo: if we stick with this, I need a purl for GARD
        curie_src = f'{prefix}:{id_src}'
        d[curie_gard] = {
            'ID': '',
            'Label': '',
            'Type': 'class',
            'Parent Class': '',
        }

    # TODO: construct a robot template
    # http://robot.obolibrary.org/template
    # Example TSV (w/ only fields that I think we'll need; 2nd row is `robot` header):
    # ID	Label	Type	Parent Class
    # ID	A rdfs:label	TYPE	SC %
    # ex:F344N	F 344/N	class	NCBITaxon:10116
    rows = list(d.values())
    robot_df = pd.DataFrame(rows)
    # todo: then prepend the robot row
    pass


if __name__ == '__main__':
    run_ingest()

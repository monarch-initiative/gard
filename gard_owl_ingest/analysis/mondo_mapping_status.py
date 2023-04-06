"""Mapping status between GARD and Mondo"""
import os
from pathlib import Path
from typing import List, Set

import pandas as pd

CURIE = str
ANALYSIS_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = ANALYSIS_DIR.parent
PROJECT_DIR = SRC_DIR.parent
DATA_DIR = PROJECT_DIR / 'data'
TMP_DIR = PROJECT_DIR / 'tmp'
DATASOURCE_CSV = DATA_DIR / 'GARD_disease_list.csv'
MONDO_SSSOM_TSV = TMP_DIR / 'mondo.sssom.tsv'


def gard_mondo_mapping_status():
    """Mapping status between GARD and Mondo"""
    gard_df = pd.read_csv(DATASOURCE_CSV)
    in_gard: List[int] = list(gard_df['GardID'])
    in_gard: Set[CURIE] = set([f'GARD:{x}' for x in in_gard])
    # todo: gard_in_mondo.txt temporary, until mondo.sssom.tsv includes GARD terms, if we ever do that
    # mondo_df = pd.read_csv(MONDO_SSSOM_TSV, sep='\t', comment='#')
    # in_mondo: Set[CURIE] = set([x for x in mondo_df['object_id'] if x.startswith('GARD:')])
    mondo_df = pd.read_csv(TMP_DIR / 'gard_in_mondo.txt', header=None)
    in_mondo: Set[CURIE] = set(mondo_df[0])

    all_ids = in_gard.union(in_mondo)
    in_mondo_not_in_gard = in_mondo.difference(in_gard)

    # todo: would ideally sort by the `int` version of GARD IDs, except for the fact that there 1 single GARD ID that
    #  is 0 padded
    df = pd.DataFrame()
    df['subject_id'] = list(all_ids)
    df['in_gard'] = df['subject_id'].isin(in_gard)
    df['in_mondo'] = df['subject_id'].isin(in_mondo)
    df['status'] = df['subject_id'].apply(lambda x:
                                          'gard' if x in in_gard and x not in in_mondo else
                                          'mondo' if x in in_mondo and x not in in_gard else
                                          'both')
    df = df.sort_values(by='subject_id')
    df.to_csv(TMP_DIR / 'gard-terms-mapping-status.csv', index=False)

    simple_df = pd.DataFrame()
    simple_df['id'] = [x.split(':')[1] for x in in_mondo_not_in_gard]
    simple_df = simple_df.sort_values(by='id')
    simple_df.to_csv(TMP_DIR / 'obsoleted-gard-terms-in-mondo.txt', index=False, header=False)


if __name__ == '__main__':
    gard_mondo_mapping_status()

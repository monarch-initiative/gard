"""Mapping status between GARD and Mondo

Outputs going online here:
https://drive.google.com/drive/folders/1jnBRzJNyShbf3vSq5ypvJYrVBiRr7iCb
"""
import os
from pathlib import Path
from typing import Dict, List, Set

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
    # Read data sources
    gard_df = pd.read_csv(DATASOURCE_CSV).fillna('')
    in_gard: List[int] = list(gard_df['GardID'])
    in_gard: Set[CURIE] = set([f'GARD:{x}' for x in in_gard])

    # todo: gard_in_mondo.txt temporary, until mondo.sssom.tsv includes GARD terms, if we ever do that
    # mondo_df = pd.read_csv(MONDO_SSSOM_TSV, sep='\t', comment='#')
    # in_mondo: Set[CURIE] = set([x for x in mondo_df['object_id'] if x.startswith('GARD:')])
    mondo_df = pd.read_csv(TMP_DIR / 'gard_in_mondo.txt', header=None)
    in_mondo: Set[CURIE] = set(mondo_df[0])

    mondo_mappings_df = pd.read_csv(MONDO_SSSOM_TSV, sep='\t', comment='#')

    # Determine overlap
    all_ids = in_gard.union(in_mondo)
    in_mondo_not_in_gard = in_mondo.difference(in_gard)

    # Geet Orphanet and OMIM (Orphanet+OMIM) mappings
    gard_ordo: Dict[str, str] = {}
    gard_omim: Dict[str, List[str]] = {}
    for row in gard_df.itertuples():
        # noinspection PyUnresolvedReferences
        if row.DataSource in ['Orphanet', 'Orphanet+OMIM']:
            # noinspection PyUnresolvedReferences
            gard_id = f'GARD:{str(row.GardID)}'
            # noinspection PyUnresolvedReferences
            gard_ordo[gard_id] = f'Orphanet:{row.SourceID}'
            # noinspection PyUnresolvedReferences
            if row.OmimMember:
                # noinspection PyUnresolvedReferences
                gard_omim[gard_id] = [f'OMIM:{x}' for x in row.OmimMember[1:-1].split(', ')]

    # Get mapping status between GARD and Mondo
    # todo: sort by the `int` of GARD IDs. Account for existence of 1 single GARD ID that is 0-padded
    df = pd.DataFrame()
    df['subject_id'] = list(all_ids)
    df['in_gard'] = df['subject_id'].isin(in_gard)
    df['in_mondo'] = df['subject_id'].isin(in_mondo)
    df['status'] = df['subject_id'].apply(
        lambda x:
        'gard' if x in in_gard and x not in in_mondo else
        'mondo' if x in in_mondo and x not in in_gard else
        'both')
    df['GARD->Orphanet'] = df['subject_id'].apply(lambda x: gard_ordo.get(x, ''))
    df['GARD->Orphanet->OMIM'] = df['subject_id'].apply(lambda x: '|'.join(gard_omim.get(x, [])))
    df = pd.merge(
        df, mondo_mappings_df[['subject_id', 'object_id']], how='left', left_on='GARD->Orphanet', right_on='object_id')\
        .rename(columns={
            'subject_id_x': 'subject_id',
            'subject_id_y': 'GARD->Orphanet->Mondo',
        }).sort_values(by='subject_id').fillna('')
    del df['object_id']
    df.to_csv(TMP_DIR / 'gard_terms_mapping_status.csv', index=False)

    # Get a list of obsolete GARD terms that are still in Mondo
    obs_gard_in_mondo_df = pd.DataFrame()
    obs_gard_in_mondo_df['id'] = [x.split(':')[1] for x in in_mondo_not_in_gard]
    obs_gard_in_mondo_df = obs_gard_in_mondo_df.sort_values(by='id')
    obs_gard_in_mondo_df.to_csv(TMP_DIR / 'obsoleted_gard_terms_in_mondo.txt', index=False, header=False)

    # Get a list of GARD terms that are not in Mondo
    # new_proxy_mappings_df: Not needed now, but could be useful at some point.
    # new_proxy_mappings_df = df[~df['in_mondo'] & (df['GARD->Orphanet->Mondo'] != '')]  # 7,690
    unmapped_df = df[df['GARD->Orphanet->Mondo'] == '']  # 3,184
    unmapped_df['subject_id'].to_csv(TMP_DIR / 'gard_unmapped_terms.txt', index=False, header=False)


if __name__ == '__main__':
    gard_mondo_mapping_status()

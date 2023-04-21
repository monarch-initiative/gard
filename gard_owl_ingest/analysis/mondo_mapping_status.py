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
TMP_INPUT_DIR = TMP_DIR / 'input'
TMP_OUTPUT_DIR = TMP_DIR / 'output'
DATASOURCE_CSV = DATA_DIR / 'GARD_disease_list.csv'
MONDO_SSSOM_TSV = TMP_INPUT_DIR / 'mondo.sssom.tsv'


# noinspection PyUnresolvedReferences Note_becausePycharmDoesntKnowAboutNamedTuples
def gard_mondo_mapping_status():
    """Mapping status between GARD and Mondo"""
    os.makedirs(TMP_INPUT_DIR, exist_ok=True)
    os.makedirs(TMP_OUTPUT_DIR, exist_ok=True)

    # Read data sources
    gard_df = pd.read_csv(DATASOURCE_CSV).fillna('')
    in_gard: List[int] = list(gard_df['GardID'])
    in_gard: Set[CURIE] = set([f'GARD:{x}' for x in in_gard])

    # gard_in_mondo.txt: Currently obtained by grep on mondo.owl and some manual ETL.
    # todo: gard_in_mondo.txt: Get via variation of mondo.sssom.tsv
    # mondo_df = pd.read_csv(MONDO_SSSOM_TSV, sep='\t', comment='#')
    # in_mondo: Set[CURIE] = set([x for x in mondo_df['object_id'] if x.startswith('GARD:')])
    mondo_df = pd.read_csv(TMP_INPUT_DIR / 'gard_in_mondo.txt', header=None)
    in_mondo: Set[CURIE] = set(mondo_df[0])

    mondo_sssom_df = pd.read_csv(MONDO_SSSOM_TSV, sep='\t', comment='#')[['subject_id', 'subject_label', 'object_id']]\
        .rename(columns={
            'subject_id': 'mondo_id',
            'subject_label': 'mondo_label',
            'object_id': 'mondo_object_id'
        })

    # Determine overlap
    all_ids = in_gard.union(in_mondo)
    in_mondo_not_in_gard = in_mondo.difference(in_gard)

    # Geet Orphanet and OMIM (Orphanet+OMIM) mappings
    gard_ordo_exact: Dict[str, str] = {}
    gard_ordo_broad: Dict[str, List[str]] = {}
    gard_omim_exact: Dict[str, str] = {}
    gard_omim_narrow: Dict[str, List[str]] = {}
    gard_omim_related: Dict[str, List[str]] = {}
    for row in gard_df.itertuples():
        gard_id = f'GARD:{str(row.GardID)}'
        # There are only 3 data sources - joeflack4
        if row.DataSource == 'Orphanet':
            # OmimMember: On 2023/04/21, for these rows, was 0 to many. Assuming narrow; but will consult. - joeflack4
            gard_ordo_exact[gard_id] = f'Orphanet:{row.SourceID}'
            mims: List[CURIE] = [f'OMIM:{x}' for x in row.OmimMember[1:-1].split(', ')] if row.OmimMember else []
            if mims:
                gard_omim_narrow[gard_id] = mims
        elif row.DataSource == 'Orphanet+OMIM':
            # OmimMember: On 2023/04/21, for all of these rows, was only 1 OmimMember and  was the same as row.SourceID
            gard_omim_exact[gard_id] = f'OMIM:{row.SourceID}'
        elif row.DataSource == 'GARD':
            # OmimMember: On 2023/04/21, 10 rows where row.DataSource == 'GARD'. 5 had OmimMembers; all only had 1 entry
            mims: List[CURIE] = [f'OMIM:{x}' for x in row.OmimMember[1:-1].split(', ')] if row.OmimMember else []
            if mims:
                gard_omim_related[gard_id] = mims
        # todo: ordo_parents: What about when DataSource == 'GARD'? Will ParentOrphaCode ever exist? Should these marked
        #  as related instead of broad? Currently, I believe no cases like this though, but should double check.
        ordo_parents: List[CURIE] = \
            [f'Orphanet:{x}' for x in row.ParentOrphaCode[1:-1].split(', ')] if row.ParentOrphaCode else []
        if ordo_parents:
            gard_ordo_broad[gard_id] = ordo_parents

    # Get explicit, existing mapping status between GARD and Mondo
    # todo: sort by the `int` of GARD IDs. Account for existence of 1 single GARD ID that is 0-padded
    existing_df = pd.DataFrame()
    existing_df['subject_id'] = list(all_ids)
    existing_df['in_gard'] = existing_df['subject_id'].isin(in_gard)
    existing_df['in_mondo'] = existing_df['subject_id'].isin(in_mondo)
    existing_df['status'] = existing_df['subject_id'].apply(
        lambda x:
        'gard' if x in in_gard and x not in in_mondo else
        'mondo' if x in in_mondo and x not in in_gard else
        'both')
    existing_df.to_csv(TMP_OUTPUT_DIR / 'gard_terms_mapping_status.csv', index=False)

    # Get proxy mappings between GARD and Mondo, through Orphanet and OMIM
    rows = []
    # todo: include: prefix_map etc as comment
    # todo: include: cols: subject_label, mapping_justification, mondo_label
    for s, o in gard_ordo_exact.items():
        rows.append({
            'subject_id': s,
            'predicate_id': 'skos:exactMatch',
            'object_id': o,
        })
    for s, o in gard_omim_exact.items():
        rows.append({
            'subject_id': s,
            'predicate_id': 'skos:exactMatch',
            'object_id': o,
        })
    for s, o_list in gard_ordo_broad.items():
        for o in o_list:
            rows.append({
                'subject_id': s,
                'predicate_id': 'skos:broadMatch',
                'object_id': o,
            })
    for s, o_list in gard_omim_narrow.items():
        for o in o_list:
            rows.append({
                'subject_id': s,
                'predicate_id': 'skos:narrowMatch',
                'object_id': o,
            })
    for s, o_list in gard_omim_related.items():
        for o in o_list:
            rows.append({
                'subject_id': s,
                'predicate_id': 'skos:relatedMatch',
                'object_id': o,
            })
    gard_sssom_df = pd.DataFrame(rows)
    gard_sssom_df2 = pd.merge(
        gard_sssom_df, mondo_sssom_df, how='left', left_on='object_id', right_on='mondo_object_id').fillna('')\
        .sort_values(by='subject_id')
    del gard_sssom_df2['mondo_object_id']
    gard_sssom_df2.to_csv(TMP_OUTPUT_DIR / 'gard.sssom.tsv', index=False, sep='\t')

    # Get a list of obsolete GARD terms that are still in Mondo
    obs_gard_in_mondo_df = pd.DataFrame()
    obs_gard_in_mondo_df['id'] = [x.split(':')[1] for x in in_mondo_not_in_gard]
    obs_gard_in_mondo_df = obs_gard_in_mondo_df.sort_values(by='id')
    obs_gard_in_mondo_df.to_csv(TMP_OUTPUT_DIR / 'obsoleted_gard_terms_in_mondo.txt', index=False, header=False)

    # Get a list of GARD terms that are not in Mondo
    unmapped_df = gard_sssom_df2[gard_sssom_df2['mondo_id'] == '']
    unmapped_ids = unmapped_df['subject_id'].unique()  # 2023/04/21: n=193
    unmapped_df = pd.DataFrame()
    unmapped_df['subject_id'] = unmapped_ids
    unmapped_df.to_csv(TMP_OUTPUT_DIR / 'gard_unmapped_terms.txt', index=False, header=False)
    return


if __name__ == '__main__':
    gard_mondo_mapping_status()

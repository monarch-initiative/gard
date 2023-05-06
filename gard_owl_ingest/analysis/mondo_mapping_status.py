"""Mapping status between GARD and Mondo

Outputs going online here:
https://drive.google.com/drive/folders/1jnBRzJNyShbf3vSq5ypvJYrVBiRr7iCb
"""
import os
import sys
from pathlib import Path
from typing import Dict, List, Set

import pandas as pd

CURIE = str
MAPPING_PREDICATE = str
ANALYSIS_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = ANALYSIS_DIR.parent
PROJECT_DIR = SRC_DIR.parent
DATA_DIR = PROJECT_DIR / 'data'
TMP_DIR = PROJECT_DIR / 'tmp'
TMP_INPUT_DIR = TMP_DIR / 'input'
OUT_DIR = DATA_DIR / 'analysis_outputs'
DATASOURCE_CSV = DATA_DIR / 'GARD_disease_list.csv'
MONDO_SSSOM_TSV = TMP_INPUT_DIR / 'mondo.sssom.tsv'
GARD_MONDO_SSSOM_TSV = TMP_INPUT_DIR / 'mondo_hasdbxref_gard.sssom.tsv'
MAPPING_PREDICATES: List[MAPPING_PREDICATE] = [
    'skos:exactMatch', 'skos:narrowMatch', 'skos:broadMatch', 'skos:relatedMatch']

# todo: move this into gard_owl_ingest.py
# noinspection PyUnresolvedReferences Note_becausePycharmDoesntKnowAboutNamedTuples
def gard_native_mappings(df: pd.DataFrame = None) -> Dict[CURIE, Dict[MAPPING_PREDICATE, List[CURIE]]]:
    """From GARD source data, get mappings categorized by type of mapping"""
    df = df if df is not None else pd.read_csv(DATASOURCE_CSV).fillna('')
    in_gard: List[int] = list(df['GardID'])
    in_gard: Set[CURIE] = set([f'GARD:{x}' for x in in_gard])
    mappings = {k: {p: [] for p in MAPPING_PREDICATES} for k in in_gard}
    for row in df.itertuples():
        gard_id = f'GARD:{str(row.GardID)}'
        # There are only 3 data sources - joeflack4
        if row.DataSource == 'Orphanet':
            # OmimMember: On 2023/04/21, for these rows, was 0 to many. Assuming narrow; but will consult. - joeflack4
            mappings[gard_id]['skos:exactMatch'].append(f'Orphanet:{row.SourceID}')
            mims: List[CURIE] = [f'OMIM:{x}' for x in row.OmimMember[1:-1].split(', ')] if row.OmimMember else []
            if mims:
                mappings[gard_id]['skos:narrowMatch'].extend(mims)
        elif row.DataSource == 'Orphanet+OMIM':
            # OmimMember: On 2023/04/21, for all of these rows, was only 1 OmimMember and  was the same as row.SourceID
            mappings[gard_id]['skos:exactMatch'].append(f'OMIM:{row.SourceID}')
        elif row.DataSource == 'GARD':
            # OmimMember: On 2023/04/21, 10 rows where row.DataSource == 'GARD'. 5 had OmimMembers; all only had 1 entry
            mims: List[CURIE] = [f'OMIM:{x}' for x in row.OmimMember[1:-1].split(', ')] if row.OmimMember else []
            if mims:
                mappings[gard_id]['skos:relatedMatch'].extend(mims)
        # todo: ordo_parents: What about when DataSource == 'GARD'? Will ParentOrphaCode ever exist? Should these marked
        #  as related instead of broad? Currently, I believe no cases like this though, but should double check.
        ordo_parents: List[CURIE] = \
            [f'Orphanet:{x}' for x in row.ParentOrphaCode[1:-1].split(', ')] if row.ParentOrphaCode else []
        if ordo_parents:
            mappings[gard_id]['skos:broadMatch'].extend(ordo_parents)

    return mappings


def gard_mondo_mapping_status():
    """Mapping status between GARD and Mondo"""
    os.makedirs(TMP_INPUT_DIR, exist_ok=True)
    os.makedirs(OUT_DIR, exist_ok=True)

    # Read data sources
    gard_df = pd.read_csv(DATASOURCE_CSV).fillna('')
    in_gard: List[int] = list(gard_df['GardID'])
    in_gard: Set[CURIE] = set([f'GARD:{x}' for x in in_gard])

    gard_mondo_sssom_df = pd.read_csv(GARD_MONDO_SSSOM_TSV, sep='\t', comment='#')[
        ['subject_id', 'subject_label', 'object_id']].fillna('').rename(columns={
            'subject_id': 'mondo_id',
            'subject_label': 'mondo_label',
            'object_id': 'gard_id'
        })
    in_mondo_sssom: Set[CURIE] = set(gard_mondo_sssom_df['gard_id'].tolist())
    # - remove 0-padding which is now longer cannonical for GARD IDs:
    in_mondo = set(['GARD:' + str(int(x.split(':')[1])) for x in in_mondo_sssom])

    mondo_sssom_df = pd.read_csv(MONDO_SSSOM_TSV, sep='\t', comment='#')[['subject_id', 'subject_label', 'object_id']]\
        .fillna('').rename(columns={
            'subject_id': 'mondo_id',
            'subject_label': 'mondo_label',
            'object_id': 'mondo_object_id'
        })

    # Determine overlap
    all_ids = in_gard.union(in_mondo)
    in_mondo_not_in_gard = in_mondo.difference(in_gard)

    # Get Orphanet and OMIM (Orphanet+OMIM) mappings
    mappings: Dict[CURIE: Dict[MAPPING_PREDICATE, List[CURIE]]] = gard_native_mappings(gard_df)

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
    existing_df = existing_df.sort_values(['status', 'subject_id', 'in_gard', 'in_mondo'])
    existing_gard_mondo_mappings: List[CURIE] = existing_df[existing_df['status'] == 'both']['subject_id'].tolist()
    existing_df.to_csv(OUT_DIR / 'gard_terms_mapping_status.csv', index=False)

    # gard.sssom.tsv
    # - Add proxy mappings between GARD and Mondo, through Orphanet and OMIM
    rows = []
    # todo: include: prefix_map etc as comment
    # todo: include: cols: subject_label, mapping_justification
    for s, xref_dict in mappings.items():
        for p, o_list in xref_dict.items():
            for o in o_list:
                rows.append({
                    'subject_id': s,
                    'predicate_id': p,
                    'object_id': o,
                })
    gard_sssom_proxy_df = pd.DataFrame(rows)
    gard_sssom_proxy_df2 = pd.merge(
        gard_sssom_proxy_df, mondo_sssom_df, how='left', left_on='object_id', right_on='mondo_object_id').fillna('')\
        .sort_values(by='subject_id')
    del gard_sssom_proxy_df2['mondo_object_id']
    gard_sssom_proxy_df2['gard_mondo_mapping_type'] = gard_sssom_proxy_df2.apply(
        lambda x: 'proxy_existing' if x.subject_id in existing_gard_mondo_mappings
        else 'proxy_new' if x.mondo_id != '' else 'unmapped_proxy_or_direct', axis=1)
    # - Filter: proxy_existing: Because proxy info not needed for existing mappings to be concatenated
    gard_sssom_proxy_df3 = gard_sssom_proxy_df2[gard_sssom_proxy_df2['gard_mondo_mapping_type'] != 'proxy_existing']
    # - Add existing mappings
    rows = []
    for row in gard_mondo_sssom_df.itertuples():
        rows.append({
            'subject_id': row.gard_id,
            'predicate_id': '',
            'object_id': '',
            'mondo_id': row.mondo_id,
            'mondo_label': row.mondo_label,
            'gard_mondo_mapping_type': 'direct_existing',
        })
    gard_sssom_direct_df = pd.DataFrame(rows)
    # todo: ideally, would sort proxy_new -> unmapped... -> direct_existing
    # todo: ideally would have last 3 col order: gard_mondo_mapping_type, mondo_id, mondo_label
    gard_sssom_df = pd.concat([gard_sssom_proxy_df3, gard_sssom_direct_df])\
        .sort_values(['gard_mondo_mapping_type', 'subject_id', 'predicate_id', 'object_id', 'mondo_id', 'mondo_label'])
    gard_sssom_df.to_csv(OUT_DIR / 'gard-mondo.sssom-like.tsv', index=False, sep='\t')

    # Get a list of obsolete GARD terms that are still in Mondo
    obs_gard_in_mondo_df = pd.DataFrame()
    obs_gard_in_mondo_df['id'] = sorted([x for x in in_mondo_not_in_gard])
    obs_gard_in_mondo_df = obs_gard_in_mondo_df.sort_values(by='id')
    obs_gard_in_mondo_df.to_csv(OUT_DIR / 'obsoleted_gard_terms_in_mondo.txt', index=False, header=False)

    # - Get a list of GARD terms that are not in Mondo
    unmapped_df = gard_sssom_df[gard_sssom_df['gard_mondo_mapping_type'] == 'unmapped_proxy_or_direct']
    unmapped_ids = sorted(unmapped_df['subject_id'].unique())  # 181
    unmapped_df2 = pd.DataFrame()
    unmapped_df2['subject_id'] = unmapped_ids
    unmapped_df2 = unmapped_df2.sort_values(by='subject_id')
    unmapped_df2.to_csv(OUT_DIR / 'gard_unmapped_terms.txt', index=False, header=False)

    # Report
    print(f'Unmapped GARD terms: {len(unmapped_ids)} of {len(gard_df)} '
          f'({round(len(unmapped_ids) / len(gard_df) * 100, 2)}%)')
    print(f'Mapped GARD terms: {len(gard_df) - len(unmapped_ids)} of {len(gard_df)} '
          f'({round((len(gard_df) - len(unmapped_ids)) / len(gard_df) * 100, 2)}%)')
    return


if __name__ == '__main__':
    try:
        gard_mondo_mapping_status()
    except FileNotFoundError as e:
        print(e)
        print('To resolve any missing files, run: make download_inputs', file=sys.stderr)

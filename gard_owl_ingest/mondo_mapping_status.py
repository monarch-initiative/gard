"""Mapping status between GARD and Mondo

Outputs going online here:
https://drive.google.com/drive/folders/1jnBRzJNyShbf3vSq5ypvJYrVBiRr7iCb
"""
import os
import sys
from typing import Dict, List, Set, Tuple

import pandas as pd

from gard_owl_ingest.utils import write_tsv_with_comments

sys.path.insert(0, os.getcwd())
from gard_owl_ingest.config import ANALYSIS_OUTDIR, CURIE, DATASOURCE_CSV, GARD_MONDO_OLD_SSSOM_TSV, MAPPING_PREDICATE, \
    MAPPING_PREDICATES, MONDO_SSSOM_METADATA_PATH, MONDO_SSSOM_TSV, RELEASE_DIR


# todo: move this into gard_owl_ingest.py
# noinspection PyUnresolvedReferences Note_becausePycharmDoesntKnowAboutNamedTuples
def get_gard_native_mappings(df: pd.DataFrame = None) -> Dict[CURIE, Dict[MAPPING_PREDICATE, List[CURIE]]]:
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


# todo: it's a bit wonky how this returns something that is used later, yet has other outputs
# todo: should each dataframe (at least that gets saved to disk) be its own function?
def gard_mondo_mapping_status(
    return_type=['sssom', 'analysis'][0], verbose=False, mondo_predicate_filter: List[str] = None,
    gard_predicate_filter: List[str] = None,
) -> pd.DataFrame | Tuple[pd.DataFrame]:
    """Mapping status between GARD and Mondo

    Side effects:
    - Saves several files"""
    file_suffix = '' if not mondo_predicate_filter and not gard_predicate_filter \
        else '-exact' if mondo_predicate_filter == ['skos:exactMatch'] and gard_predicate_filter == ['skos:exactMatch'] \
        else '-custom'
    # Read data sources
    gard_df = pd.read_csv(DATASOURCE_CSV).fillna('')
    gard_in_gard: List[int] = list(gard_df['GardID'])
    gard_in_gard: Set[CURIE] = set([f'GARD:{x}' for x in gard_in_gard])

    gard_mondo_sssom_from_mondo_df = pd.read_csv(GARD_MONDO_OLD_SSSOM_TSV, sep='\t', comment='#').fillna('').rename(
        columns={
            'subject_id': 'mondo_id',
            'subject_label': 'mondo_label',
            'object_id': 'gard_id'
        })
    gard_in_mondo_sssom: Set[CURIE] = set(gard_mondo_sssom_from_mondo_df['gard_id'].tolist())
    # - remove 0-padding which is now longer cannonical for GARD IDs:
    gard_in_mondo = set(['GARD:' + str(int(x.split(':')[1])) for x in gard_in_mondo_sssom])

    mondo_sssom_df = pd.read_csv(MONDO_SSSOM_TSV, sep='\t', comment='#')  # n=73,320
    # - filter mondo.sssom.tsv: only exactMatch
    #   - per https://github.com/monarch-initiative/gard/pull/10#issuecomment-1588881615
    #   - analysis:
    # mondo_etc = mondo_sssom_df[~(mondo_sssom_df['predicate_id'] == 'skos:exactMatch')]  # n=77
    # mondo_broad = mondo_sssom_df[mondo_sssom_df['predicate_id'] == 'skos:broadMatch']  # n=77 (all non-exact = broad)
    # mondo_sssom_df = mondo_sssom_df[mondo_sssom_df['predicate_id'] == 'skos:exactMatch']  # n=73,243
    if mondo_predicate_filter:
        mondo_sssom_df = mondo_sssom_df[mondo_sssom_df['predicate_id'].isin(mondo_predicate_filter)]
    mondo_sssom_df = mondo_sssom_df[['subject_id', 'subject_label', 'predicate_id', 'object_id']]\
        .fillna('').rename(columns={
            'subject_id': 'mondo_id',
            'subject_label': 'mondo_label',
            'object_id': 'mondo_object_id',
            'predicate_id': 'mondo_predicate_id',
        })

    # Determine overlap
    gard_all_ids = gard_in_gard.union(gard_in_mondo)

    # obsoleted_gard_terms_in_mondo.txt: get a list of obsolete GARD terms that are still in Mondo
    # todo: code smell: this runs twice since gard_owl_ingest.py calls this func twice, one with filter. but this
    #  doesn't change either time. it just gets re-written.
    in_mondo_not_in_gard = gard_in_mondo.difference(gard_in_gard)
    obs_gard_in_mondo_df = pd.DataFrame()
    obs_gard_in_mondo_df['id'] = sorted([x for x in in_mondo_not_in_gard])
    obs_gard_in_mondo_df = obs_gard_in_mondo_df.sort_values(by='id')
    obs_gard_in_mondo_df.to_csv(ANALYSIS_OUTDIR / 'obsoleted_gard_terms_in_mondo.txt', index=False, header=False)

    # Get Orphanet and OMIM (Orphanet+OMIM) mappings
    gard_native_mappings: Dict[CURIE: Dict[MAPPING_PREDICATE, List[CURIE]]] = get_gard_native_mappings(gard_df)
    if gard_predicate_filter:
        for gard_id, pred_mappings in gard_native_mappings.items():
            for pred in list(pred_mappings.keys()):
                if pred not in gard_predicate_filter:
                    del pred_mappings[pred]

    # gard_terms_mapping_status.csv: get explicit, existing mapping status between GARD and Mondo
    # - these are mappings at the time before we began the GARD ingest, and we this was useful for analytical
    #   information at the time, but we maybe should drop this because not using for curation. We're not keeping the
    #   previous Mondo::GARD mappings from Mondo.
    # todo: sort by the `int` of GARD IDs. Account for existence of 1 single GARD ID that is 0-padded
    # todo: maybe this file should be renamed. we are dropping old existing mondo::gard mappings
    existing_df = pd.DataFrame()
    existing_df['subject_id'] = list(gard_all_ids)
    existing_df['in_gard'] = existing_df['subject_id'].isin(gard_in_gard)
    existing_df['in_mondo'] = existing_df['subject_id'].isin(gard_in_mondo)
    existing_df['status'] = existing_df['subject_id'].apply(
        lambda x:
        'gard' if x in gard_in_gard and x not in gard_in_mondo else
        'mondo' if x in gard_in_mondo and x not in gard_in_gard else
        'both')
    existing_df = existing_df.sort_values(['status', 'subject_id', 'in_gard', 'in_mondo'])
    existing_gard_mondo_mappings: List[CURIE] = existing_df[existing_df['status'] == 'both']['subject_id'].tolist()
    existing_df.to_csv(ANALYSIS_OUTDIR / f'gard_terms_mapping_status{file_suffix}.csv', index=False)

    # gard-mondo.sssom.tsv: (i) GARD::Mondo mappings via proxy (Orphanet/OMIM), (ii) keep unmapped
    # todo: should everything for gard-mondo.sssom.tsv be its own function?
    # - sssom_proxyable_df: GARD::proxy mappings. Native from GARD.
    rows = []
    for s, xref_dict in gard_native_mappings.items():
        for p, o_list in xref_dict.items():
            for o in o_list:
                rows.append({
                    'subject_id': s,
                    'predicate_id': p,
                    'object_id': o,
                })
    sssom_proxyable_df = pd.DataFrame(rows)

    # - sssom_proxy_df: GARD::Mondo JOINed mappings via proxy (Orphanet/OMIM)
    proxy_and_unmapped_df = pd.merge(
        sssom_proxyable_df, mondo_sssom_df, how='left', left_on='object_id', right_on='mondo_object_id').fillna('')\
        .sort_values(by='subject_id')
    del proxy_and_unmapped_df['mondo_object_id']
    proxy_and_unmapped_df['mapping_justification'] = 'semapv:ManualMappingCuration'
    # - proxy_existing: These were mappings that were made from Mondo to GARD before. We're likely going to ignore these
    # completely. But every term on this list also is able to have a new proxy mapping between GARD and Mondo using our
    # new algorithmic methods here.
    # - unmapped: It's possible there may have been some previous Mondo::GARD mappings that were mapped that are
    # actually in this list, but we are ignoring those now.
    proxy_and_unmapped_df['gard_mondo_mapping_type'] = proxy_and_unmapped_df.apply(
        lambda x: 'unmapped' if x.mondo_id == ''
        else 'proxy_existing' if x.subject_id in existing_gard_mondo_mappings
        else 'proxy_new', axis=1)

    # todo: temp until unit test
    # - testing
    test_proxy_unmapped_gard = set(
        proxy_and_unmapped_df[proxy_and_unmapped_df['gard_mondo_mapping_type'] == 'unmapped']['object_id'])
    test_proxy_unmapped_mondo = set(mondo_sssom_df['mondo_object_id'])
    assert len(test_proxy_unmapped_mondo.intersection(test_proxy_unmapped_gard)) == 0

    # - Add existing mappings
    rows = []
    for row in gard_mondo_sssom_from_mondo_df.itertuples():
        # noinspection PyUnresolvedReferences pycharm_doesnt_recognize_tuple_props
        rows.append({
            'subject_id': row.gard_id,
            'predicate_id': row.predicate_id,
            'object_id': row.mondo_id,
            'mondo_id': row.mondo_id,
            'mondo_label': row.mondo_label,
            'mapping_justification': row.mapping_justification,
            'gard_mondo_mapping_type': 'direct_existing',
        })
    sssom_direct_df = pd.DataFrame(rows)
    # todo: ideally, would sort proxy_new -> unmapped... -> direct_existing
    # todo: ideally would have last 3 col order: gard_mondo_mapping_type, mondo_id, mondo_label
    sssom_like_df = pd.concat([proxy_and_unmapped_df, sssom_direct_df]).sort_values([
        'gard_mondo_mapping_type', 'subject_id', 'predicate_id', 'object_id', 'mondo_id', 'mondo_label',
        'mapping_justification']).fillna('')
    sssom_like_df.to_csv(ANALYSIS_OUTDIR / f'gard-mondo.sssom-like{file_suffix}.tsv', index=False, sep='\t')

    # - create gard-mondo_curation.sssom.tsv
    sssom_curate_df = sssom_like_df[sssom_like_df['gard_mondo_mapping_type'] != 'unmapped']
    sssom_curate_df = sssom_curate_df[sssom_curate_df['gard_mondo_mapping_type'] != 'direct_existing']
    sssom_curate_df = sssom_curate_df[[col for col in sssom_curate_df.columns if col != 'gard_mondo_mapping_type']]
    sssom_curate_df = sssom_curate_df.rename(columns={'object_id': 'proxy_id', 'mondo_id': 'object_id', 'mondo_label': 'object_label'})
    sssom_curate_df = sssom_curate_df.reindex(columns=[
        'subject_id', 'predicate_id', 'object_id', 'object_label', 'mapping_justification', 'proxy_id',
        'mondo_predicate_id'])

    # - create gard-mondo.sssom.tsv
    # TODO @Nico: verify: that algorithm is sound, if we're even going to continue doing this algorithmically
    # todo: relatedMatch will likely be removed or replaced
    proxy_mappings: Dict[CURIE, Dict[MAPPING_PREDICATE, List[Dict]]] = {}
    for _index, row in sssom_curate_df.iterrows():
        row = dict(row)
        if row['subject_id'] not in proxy_mappings:
            proxy_mappings[row['subject_id']] = {}
        if row['predicate_id'] not in proxy_mappings[row['subject_id']]:
            proxy_mappings[row['subject_id']][row['predicate_id']] = []
        proxy_mappings[row['subject_id']][row['predicate_id']].append(row)
    chosen_mappings: Dict[CURIE, Dict] = {}
    for term, mappings_by_pred in proxy_mappings.items():
        preds = set(mappings_by_pred.keys())
        # a. complex algorithm
        # todo: remove these comments if not needed
        # if preds == {'skos:narrowMatch', 'skos:exactMatch', 'skos:broadMatch'}:
        #     pass
        # elif preds == {'skos:narrowMatch', 'skos:broadMatch'}:
        #     pass
        # elif preds == {'skos:narrowMatch', 'skos:exactMatch'}:
        #     pass
        # elif preds == {'skos:exactMatch', 'skos:broadMatch'}:
        #     pass
        # b. simple algorithm
        pred = 'skos:exactMatch' if 'skos:exactMatch' in preds \
            else 'skos:narrowMatch' if 'skos:narrowMatch' in preds \
            else 'skos:broadMatch' if 'skos:broadMatch' in preds \
            else 'skos:relatedMatch'
        chosen_mappings[term] = mappings_by_pred[pred][0]

    # - sssom_df: Has less rows because of 'chosen mappings'. Just keeping 1 edge
    sssom_df = pd.DataFrame(chosen_mappings.values())

    # - modify & save curation df
    sssom_curate_df = sssom_curate_df.drop('mapping_justification', axis=1)\
        .sort_values(by=['predicate_id', 'subject_id'])
    outpath_mondo_sssom_curate = RELEASE_DIR / f'gard-mondo{file_suffix}_curation.sssom.tsv'
    write_tsv_with_comments(sssom_curate_df, MONDO_SSSOM_METADATA_PATH, outpath_mondo_sssom_curate)

    # - mondo-gard.robot.template.sssom.tsv
    robot_df = sssom_df.drop(columns=['mondo_predicate_id'])\
        .sort_values(by=['object_id', 'subject_id', 'proxy_id'])\
        .rename(columns={
            'subject_id': 'gard_id',
            'object_id': 'mondo_id',
            'proxy_id': 'source_external',
            'predicate_id': 'source_type',
            'object_label': 'mondo_label',
        })
    del robot_df['source_type']
    del robot_df['mondo_label']
    # robot_df['source_type'] = robot_df['source_type'].apply(
    #     lambda x: x.replace('skos:exactMatch', 'MONDO:equivalentTo'))
    robot_df['type'] = 'owl:Class'
    robot_df['subset'] = 'http://purl.obolibrary.org/obo/mondo#gard_rare'
    robot_subheader = [{
        'mondo_id': 'ID',
        'type': 'TYPE',
        'gard_id': 'A oboInOwl:hasDbXref',
        'source_external': '>A oboInOwl:source',
        'subset': 'AI oboInOwl:inSubset',
        # 'source_type': '>A oboInOwl:source',
        # 'object_label': '',
    }]
    robot_df = pd.concat([pd.DataFrame(robot_subheader), robot_df])[list(robot_subheader[0].keys())]
    outpath_mondo_robot_sssom = RELEASE_DIR / f'mondo-gard{file_suffix}.robot.template.sssom.tsv'
    write_tsv_with_comments(robot_df, MONDO_SSSOM_METADATA_PATH, outpath_mondo_robot_sssom)

    # - sssom_df: save
    # - Has less rows because of 'chosen mappings'. Just keeping 1 edge
    sssom_df = sssom_df.drop(columns=['proxy_id', 'mondo_predicate_id']).sort_values(by=['predicate_id', 'subject_id'])
    outpath_mondo_sssom = RELEASE_DIR / f'gard-mondo{file_suffix}.sssom.tsv'
    write_tsv_with_comments(sssom_df, MONDO_SSSOM_METADATA_PATH, outpath_mondo_sssom)

    # gard_unmapped_terms.txt: get a list of GARD terms that are not in Mondo
    # todo: can I get this information from sssom_curate_df? if so, I could maybe put this code in calling func
    unmapped_ids: List[CURIE] = \
        proxy_and_unmapped_df[proxy_and_unmapped_df['gard_mondo_mapping_type'] == 'unmapped']['subject_id'].tolist()
    unmapped_any_df2 = pd.DataFrame({'subject_id': unmapped_ids}).sort_values(by='subject_id')
    unmapped_any_df2.to_csv(ANALYSIS_OUTDIR / f'gard_unmapped_terms{file_suffix}.txt', index=False, header=False)
    # - report
    if verbose:
        print(f'Unmapped GARD terms: {len(unmapped_ids)} of {len(gard_df)} '
              f'({round(len(unmapped_ids) / len(gard_df) * 100, 2)}%)')
        print(f'Mapped GARD terms: {len(gard_df) - len(unmapped_ids)} of {len(gard_df)} '
              f'({round((len(gard_df) - len(unmapped_ids)) / len(gard_df) * 100, 2)}%)')

    if return_type == 'sssom':
        return sssom_curate_df
    elif return_type == 'analysis':
        return proxy_and_unmapped_df, sssom_curate_df


if __name__ == '__main__':
    try:
        gard_mondo_mapping_status()
    except FileNotFoundError as e:
        print(e)
        print('To resolve any missing files, run: make download_inputs', file=sys.stderr)

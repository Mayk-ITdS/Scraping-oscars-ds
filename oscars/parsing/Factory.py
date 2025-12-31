from pathlib import Path

import pandas as pd
import re
from oscars.parsing.normalizers import norm_entity, split_entity_col, norm_role
from oscars.utils.my_functions import ensure_schema_min, subtract_generic_by_priority
from src.pipeline import TRANSFORMED

_WS = re.compile(r'\s+')
SUFFIX_TOK = r'(?:Jr|Sr|I{2,3}|IV|V)\.?'
CORP_SFX = r'(?:Inc\.?|Incorporated|Ltd|LLC|L\.L\.C\.|LLP|PLC|S\.A\.|AG|GmbH|Co\.?|Company)'

comma_not_before_suffix = r',\s*(?!(?:' + SUFFIX_TOK + r'|' + CORP_SFX + r')(?:\b|\.))'
SPLIT_PAT = r'(?:' + comma_not_before_suffix + r'|\s+(?:and|&)\s+)'

def extract_notes(df_series,pattern,pattern2,pattern3,protected_ids):
    def _preamble_to_standard(s: str) -> str:
        if not s:
            return ""
        m = pattern2.match(s)
        if not m:
            return s
        entity = (m.group('entity') or '').strip()
        tail = (m.group('note') or '').strip()
        return f"{entity} — {tail}" if tail else s

    series_normalized = df_series.astype('string').map(_preamble_to_standard)
    note_only = df_series.str.extractall(pattern3).reset_index().rename(columns={'level_0':'row_id'})
    note_only['row_id'] = note_only['row_id'].astype('int64')
    note_only['note'] = note_only['note'].str.replace(r'^\s*For\b', 'for', regex=True).str.strip()
    note_only = ensure_schema_min(note_only)
    m_pat_notes = (
            series_normalized
            .str.extractall(pattern)
            .reset_index()
            .rename(columns={'level_0': 'row_id'})
        )
    m_pat_notes['row_id'] = m_pat_notes['row_id'].astype('int64')
    if not m_pat_notes.empty:
        m_pat_notes = m_pat_notes[~m_pat_notes['row_id'].isin(protected_ids)]
        m_pat_notes['entity'] = (m_pat_notes['entity']
                                 .astype('string')
                                 .str.replace(r'\s+', ' ', regex=True)
                                 .str.strip(" ,—–-"))
        m_pat_notes['note'] = (m_pat_notes['note']
                               .astype('string')
                               .str.replace(r'\s+', ' ', regex=True)
                               .str.strip(" .!?;:,—–-"))
        m_pat_notes['role'] = (m_pat_notes['roles'].astype('string').str.replace(r'\s+', ' ', regex=True).str.strip(" .!?;:,—–-"))
        m_pat_notes = split_entity_col(m_pat_notes, 'entity')
        m_pat_notes = pd.concat([m_pat_notes,note_only])
        protected_ids.add(8320)
        protected_ids.update(m_pat_notes['row_id'].unique())
    else:
        m_pat_notes = pd.DataFrame(columns=['row_id', 'entity', 'note', 'role'])

    return m_pat_notes,protected_ids

def extract_hand_written(df_series,pattern):

    df_series = df_series.map(norm_entity)
    m_written = (
        df_series.str.extractall(pattern).reset_index()
        .rename(columns={'level_0': 'row_id'})
    )
    m_written['row_id'] = m_written['row_id'].astype('int64')
    m_written['role'] = m_written['role'].fillna(m_written['role2'])
    m_written['entity'] = m_written['entity'].fillna(m_written['entity2'])

    if not m_written.empty:
        m_written['role'] = m_written['role'].fillna('screenplay')
        m_written['note'] = pd.NA

        m_written = m_written.drop(columns=['role2', 'entity2'], errors='ignore')
        m_written['entity'] = m_written['entity'].astype('string').str.strip()
    else:
        m_written = pd.DataFrame(columns=['row_id', 'entity', 'role', 'note'])
    m_written_final = split_entity_col(m_written, 'entity')

    return m_written_final

def extract_producers(df_series,pattern,protected_ids):

    m_prod_parenteses = (df_series.str.extractall(pattern)
                         .reset_index()
                         .rename(columns={'level_0': 'row_id'}))
    # normalizacja + split wielu osób, gdyby się pojawiły
    m_prod_parenteses['row_id'] = m_prod_parenteses['row_id'].astype('int64')
    m_prod_paren = (m_prod_parenteses
                    .rename(columns={'entity': 'entity', 'role': 'role', 'note': 'note'})
                    .assign(role=lambda d: d['role'].astype('string').str.strip().str.lower())
                    )
    m_prod_paren['entity'] = m_prod_paren['entity'].astype('string').str.strip()
    m_prod_paren = split_entity_col(m_prod_paren, 'entity')

    m_prod_paren = ensure_schema_min(m_prod_paren)
    if not m_prod_paren.empty:
        protected_ids.update(m_prod_paren['row_id'].unique())

        return m_prod_paren

def extract_musical_directors(df_series,pattern):
    m_music_director = (df_series.str.extractall(pattern)
                        .reset_index()
                        .rename(columns={'level_0': 'row_id'}))
    m_music_director['row_id'] = m_music_director['row_id'].astype('int64')
    m_music_director = (m_music_director[['row_id', 'people', 'role']]
                        .rename(columns={'people': 'entity'}))
    m_music_director['entity'] = m_music_director['entity'].astype('string').str.strip()

    m_music_director = split_entity_col(m_music_director, 'entity')

    m_music_director = ensure_schema_min(m_music_director)

    return m_music_director

def extract_new_sound(df_series,pattern1,pattern2,protected_ids):

    new_sound = df_series.str.extractall(pattern1).reset_index().rename(columns={'level_0': 'row_id'})
    new_sound = ensure_schema_min(new_sound)
    new_sound['row_id'] = new_sound['row_id'].astype('int64')
    new_sound_parenthesis = df_series.str.extractall(pattern2).reset_index().rename(columns={'level_0': 'row_id'})
    new_sound_parenthesis['row_id'] = new_sound_parenthesis['row_id'].astype('int64')
    new_sound_parenthesis = ensure_schema_min(new_sound_parenthesis)
    m_new = pd.concat([new_sound,new_sound_parenthesis],ignore_index=True)

    # Porządek i typy:
    m_new['row_id'] = m_new['row_id'].astype('int64')
    m_new = m_new.sort_values(['row_id'], kind='stable').reset_index(drop=True)
    subset = [c for c in ['row_id', 'person', 'affiliation', 'role', 'entity', 'note'] if c in m_new.columns]

    m_new = m_new.drop_duplicates(
        subset=subset,
        keep='first'
    )
    ids = m_new['row_id'].dropna()

    assert ids.isin(df_series.index).all(), f"Brakujące row_id: {sorted(set(ids) - set(df_series.index))[:20]}"
    assert m_new['row_id'].isin(df_series.index).all()

    protected_ids.update(m_new['row_id'].unique())
    return m_new,protected_ids

def extract_sound(df_series,pattern1,pattern2,protected_ids):
    studios = (df_series.str.extract(pattern1).reset_index(drop=False).rename(columns={"index": "row_id"}))
    studios['row_id'] = studios['row_id'].astype('int64')
    m_studio_name = (studios[['row_id', 'studio_name']].dropna(subset=['studio_name']).rename(columns={'studio_name': 'entity'}))
    m_studio_name['entity'] = m_studio_name['entity'].astype('string').str.strip()
    m_studio_name['role'] = 'recording_studio'
    m_studio_name = ensure_schema_min(m_studio_name)
    tails = studios.dropna(subset=['studio_name'])
    mask_sound_directors = tails['sound_director'].notna()
    sd = tails.loc[mask_sound_directors, ['row_id', 'sound_director']].copy()

    sd['entity'] = (sd['sound_director'].astype('string')
                    .str.replace(r',\s*Sound\s+Director(?:s)?\b.*$', '', regex=True)
                    .str.strip())
    sd['role'] = 'sound director'

    m_sound_directors = split_entity_col(sd.loc[~sd['row_id'].isin(protected_ids), ['row_id', 'entity', 'role']],
                                          'entity')
    # studios ready
    m_sound_final = pd.concat([m_studio_name, m_sound_directors], ignore_index=True)
    m_sound_final = ensure_schema_min(m_sound_final)
    protected_ids.update(m_sound_final['row_id'].unique())

    # scenario Name Surname, Sound Director
    m_sound_segment = df_series.str.extractall(pattern2).reset_index(drop=False).rename(
        columns={'level_0': 'row_id'})
    m_sound_segment['row_id'] = m_sound_segment['row_id'].astype('int64')
    # m_sd_directors = m_sound_segment.loc[~m_sound_segment['row_id'].isin(protected_ids),['row_id', 'people']].rename(columns={'people': 'entity'})
    # m_sd_directors['entity'] = m_sd_directors['entity'].astype('string').str.strip()
    # m_sd_directors['role'] = 'sound director'
    # m_sd_directors = split_entity_col(m_sd_directors, 'entity')
    # m_sd_directors = ensure_schema_min(m_sd_directors)
    # protected_ids.update(m_sd_directors['row_id'].unique())

    return m_sound_final,protected_ids

def extract_prod(df_series, pattern):
    m_prod_roles = (
        df_series.str.extractall(pattern)
        .reset_index()
        .rename(columns={'level_0': 'row_id'})
    )
    m_prod_roles['row_id'] = m_prod_roles['row_id'].astype('int64')

    if not m_prod_roles.empty:
        m_prod_roles['entity'] = m_prod_roles['entity'].astype('string').str.strip()
        m_prod_roles['role'] = (
            m_prod_roles['role']
            .astype('string')
            .str.lower()
            .str.replace(r'\s+', ' ', regex=True)
            .replace({
                'producers': 'producer',
                'executive producers': 'executive producer',
                'associate producers': 'associate producer'
            })
        )
        m_prod_roles['entity'] = m_prod_roles['entity'].map(norm_entity)

        m_prod_roles = split_entity_col(m_prod_roles, 'entity')

        m_prod_roles = ensure_schema_min(m_prod_roles)
    else:
        m_prod_roles = pd.DataFrame(columns=['row_id', 'entity', 'role', 'note'])

    return m_prod_roles

def extract_pairs(df_series, pattern, protected_ids):
    m_pairs = (df_series.str.extractall(pattern)
               .reset_index()
               .rename(columns={'level_0': 'row_id', 'people': 'entity'}))
    m_pairs['row_id'] = m_pairs['row_id'].astype('int64')
    m_pairs = m_pairs[~m_pairs['row_id'].isin(protected_ids)]
    m_pairs['entity'] = m_pairs['entity'].astype('string').str.strip()
    m_pairs['role'] = m_pairs['role'].astype('string').str.strip().str.lower()

    m_pairs = split_entity_col(m_pairs, 'entity')
    m_pairs = ensure_schema_min(m_pairs)
    protected_ids.update(m_pairs['row_id'].unique())
    return m_pairs,protected_ids

def extract_parent_ent(df_series,pattern,protected_ids):
    m_paren_ent = (df_series.str.extractall(pattern)
                   .reset_index()
                   .rename(columns={'level_0': 'row_id'}))
    m_paren_ent['row_id'] = m_paren_ent['row_id'].astype('int64')
    m_paren_ent = m_paren_ent.drop(index=m_paren_ent.index[m_paren_ent['row_id'].isin(protected_ids)])
    if not m_paren_ent.empty:
        m_paren_ent = m_paren_ent[['row_id', 'entity']].assign(role=pd.NA)
        m_paren_ent['entity'] = m_paren_ent['entity'].astype('string').str.strip()

        m_paren_ent = ensure_schema_min(m_paren_ent)

    return m_paren_ent,protected_ids

def extract_by_parenthesis(df_series, pattern,pattern2,protected_ids):

    m_by_paren = (df_series.str.extractall(pattern)
                      .reset_index()
                      .rename(columns={'level_0': 'row_id'}))
    m_by_paren['row_id'] = m_by_paren['row_id'].astype(int)
    m_entity_before_semicolon = (df_series.str.extractall(pattern2).reset_index().rename(columns={'level_0': 'row_id'}))
    m_entity_before_semicolon['row_id'] = m_entity_before_semicolon['row_id'].astype(int)
    m_by_paren = ensure_schema_min(m_by_paren)
    m_entity_before_semicolon = ensure_schema_min(m_entity_before_semicolon)

    out = pd.concat([m_by_paren[['row_id','entity','role','note','affiliation','person']], m_entity_before_semicolon[['row_id','entity','role','note','affiliation','person']]], ignore_index=True)
    out = (out
           .sort_values(['row_id', 'entity', 'role'], kind='stable')
           .drop_duplicates(subset=['row_id', 'entity', 'role', 'note', 'affiliation', 'person'], keep='first')
           .reset_index(drop=True))
    # protected_ids.add(8320)

    ids = out['row_id'].unique()
    assert pd.Index(ids).isin(df_series.index).all(), \
        f"extract_by_parenthesis: row_id spoza indeksu left_s: {sorted(set(ids) - set(df_series.index))[:20]}"
    protected_ids.update(out['row_id'].unique())

    return out, protected_ids

def extract_foreign_lg(df_series, pattern):

    m_foreign = (df_series.str.extractall(pattern)
                 .reset_index()
                 .rename(columns={'level_0': 'row_id'}))
    m_foreign['row_id'] = m_foreign['row_id'].astype('int64')
    m_foreign = (m_foreign.assign(title=lambda d: d['title'].astype('string').str.strip(),
                                  role='movie',
                                  entity=lambda d: d['title'].astype('string').str.strip(), )
    [['row_id', 'entity', 'role', 'note']])

    m_foreign = ensure_schema_min(m_foreign)

    return m_foreign
# def assign_to_entity(df_series):
#     df = df_series.copy()
#     entity = df['entity'].astype('string').str.strip()
#     affiliation = df['affiliation'].astype('string').str.strip()
#     person = df['person'].astype('string').str.strip()
#     year = df['year'].astype('string').str.strip()
#     category = df['category'].astype('string').str.strip()
#     if category == 'Best Picture':
#         if year <= 1950:
#             df[entity] = df[affiliation]
#         elif year > 1951:
#             df[entity] = df[person]
#     categories = {
#         "Best Picture":lambda d: (d['entity'] = df['affiliation'] if d <= 1950 else d['entity] = df['person']),
#     }


def extract_head_written(df_series_1,df_series_2,df_series_3):

    m_head_final = pd.concat(
        [
            df_series_1,
            df_series_2,
        ],
        ignore_index=True
    )
    m_head_final = ensure_schema_min(m_head_final)
    m_written_final = ensure_schema_min(df_series_3)
    m_head_written_final = pd.concat([m_head_final, m_written_final], ignore_index=True).drop_duplicates()

    return m_head_written_final

def build_pri_all(base_,frames_dict, m_pat_notes, m_generic_full,year_map=None, split_pat=SPLIT_PAT):
    def _is_all_na(df: pd.DataFrame) -> bool:
        return df.empty or (df.isna().all().all() if len(df.columns) else True)

    def _ensure_min_cols(df: pd.DataFrame, cols=('row_id','entity','role','note','affiliation','person')) -> pd.DataFrame:
        df = df.copy()
        for c in cols:
            if c not in df.columns:
                df[c] = pd.NA
        return df[list(cols)]

    if year_map is None:
        if isinstance(base_, pd.DataFrame) and 'year' in base_.columns:
            year_map = base_.set_index('row_id')['year']
        else:
            raise ValueError("Przekaż year_map=Series(index=row_id, values=year) albo base_ z kolumną 'year'.")

    pri_all_list = []

    for key, f in frames_dict.items():
        tmp = f.copy()
        if 'year' not in tmp.columns:
            tmp['row_id'] = tmp['row_id'].astype('int64')
            tmp['year'] = tmp['row_id'].map(year_map)

        if key in {'new_frame', 'sd_director'} and {'person', 'affiliation'}.issubset(tmp.columns):
            person_ok = tmp['person'].astype('string').str.strip().ne('').fillna(False)
            affil_ok = tmp['affiliation'].astype('string').str.strip().ne('').fillna(False)
            pre_cut = tmp['year'].le(1950).fillna(False)

            tmp['entity'] = pd.NA
            # <=1950 traktujemy studio jako "entity"
            tmp.loc[pre_cut & affil_ok, 'entity'] = tmp.loc[pre_cut & affil_ok, 'affiliation']
            # >1950 traktujemy osobę jako "entity"
            tmp.loc[~pre_cut & person_ok, 'entity'] = tmp.loc[~pre_cut & person_ok, 'person']
            pri_all_list.append(tmp)
            continue

        if 'people' in tmp.columns:
            role_series = tmp['role'] if 'role' in tmp.columns else pd.Series([pd.NA] * len(tmp), index=tmp.index)
            out = (
                tmp[['row_id', 'people', 'year']].copy()
                .assign(entity=tmp['people'].astype('string').map(norm_entity),
                        role=role_series.astype('string').str.strip())
                .explode('entity', ignore_index=True)
            )
            out = _ensure_min_cols(out)
            pri_all_list.append(out)
            continue

        if 'entity' in tmp.columns:
            out = split_entity_col(_ensure_min_cols(tmp), 'entity')
            pri_all_list.append(out)
            continue

    if isinstance(m_pat_notes, pd.DataFrame) and not _is_all_na(m_pat_notes):
        pri_all_list.insert(0, _ensure_min_cols(m_pat_notes, ('row_id','entity','role','note','affiliation','person')))

    if pri_all_list:
        pri_all = pd.concat(pri_all_list, ignore_index=True)
    else:
        pri_all = pd.DataFrame(columns=['row_id','entity','role','note'])

    pri_all = ensure_schema_min(pri_all)
    with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 200):
        pri_all.to_csv( TRANSFORMED / "pri_all.csv", index=False)

    pri_all['role'] =  (pri_all['role'].astype('string').fillna("").str.split(r'\s*,\s*'))

    pri_all = pri_all.explode('role',ignore_index=True)

    pri_all['role'] = pri_all['role'].astype('string').str.strip().replace({"": pd.NA})

    # normalizacja
    pri_all['role']   = pri_all['role'].astype('string').str.strip().map(norm_role)
    pri_all['entity'] = pri_all['entity'].astype('string').map(norm_entity)

    ROLE_WORDS = {
        'writer', 'director', 'performer', 'pioneer', 'producer',
        'actor', 'actress', 'composer', 'cinematographer', 'editor'
    }
    mask_roles = pri_all['entity'].str.lower().isin(ROLE_WORDS)
    if mask_roles.any():
        role_map = (
            pri_all[mask_roles]
            .groupby('row_id')['entity']
            .apply(lambda x: ', '.join(sorted(set(x.str.lower()))))
            .to_dict()
        )
        def merge_roles(row):
            base = str(row['role']) if pd.notna(row['role']) else ''
            extras = role_map.get(row['row_id'], '')
            return ', '.join(filter(None, [base.strip(', '), extras.strip(', ')]))

        idx = pri_all['row_id'].isin(role_map.keys())
        pri_all.loc[idx, 'role'] = pri_all.loc[idx].apply(merge_roles, axis=1)
        pri_all = pri_all[~mask_roles]

    # redukcja m_generic
    m_generic_full = subtract_generic_by_priority(m_generic_full, pri_all, norm_entity)

    return m_generic_full, pri_all

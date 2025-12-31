from __future__ import annotations
import re
from pathlib import Path
import pandas as pd
from pandas import DataFrame
from oscars.parsing.Factory import extract_pairs, extract_new_sound
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
# pd.set_option('display.max_colwidth', None)
ROOT = Path(__file__).resolve().parents[2]
TRANSFORMED = ROOT / "analitics" / "transformed"

KEY = ['year','link','category','object','is_winner']

def extract_title_and_left(df: DataFrame) -> DataFrame:

    titles = (df["object"]
              .astype("string")
              .str.extract(re.compile(r'''(?xi)[-–—]\s*["“‘\'](?P<title>.*)["”’]\s*$''')))
    df["title"] = titles['title'].astype('string').str.strip()
    df["left"] = (df["object"].astype("string")
                  .str.replace(r'[ \-–—]*"[^"]+"[^"]*$', '', regex=True).str.rstrip(" -–—")
                  .str.strip())
    left_s = df["left"].astype("string")
    no_colon = ~left_s.str.contains(":", na=False)
    no_comma = ~left_s.str.contains(",", na=False)
    no_srednik = ~left_s.str.contains(";", na=False)
    df["person_fallback"] = left_s.where(df["title"].notna() & no_colon & no_comma & no_srednik)

    return df

def extract_roles_by_person(df: DataFrame) -> DataFrame:
    import pandas as pd
    from oscars.utils.my_functions import (
        ensure_schema_min
    )
    from oscars.parsing.Factory import (

        extract_notes, extract_hand_written, extract_producers, extract_musical_directors,
        extract_sound, extract_prod, extract_parent_ent, extract_by_parenthesis,
        extract_foreign_lg, extract_head_written, build_pri_all
    )
    from oscars.parsing.normalizers import norm_entity, norm_role, split_entity_col,split_keep_protected
    from oscars.parsing.RegexPatterns import RegexPatterns
    from oscars.utils.my_functions import audit_overlaps

    # Canonicalization function
    if df.index.name == 'row_id':
        df = df.reset_index()
    elif 'row_id' not in df.columns:
        df['row_id'] = df.index.astype('int64')

    base = df.copy()
    left_s = base['left'].astype('string').fillna('').str.strip()
    protected_ids = set()

    m_prod_paren = extract_producers(left_s, RegexPatterns.all()['producers'], protected_ids)
    # all parenthesis factory
    m_by_paren,protected_ids = extract_by_parenthesis(left_s, RegexPatterns.all()['role_by_paren'],RegexPatterns.Studio.pat_leading_entity_before_semicolon,protected_ids)

    # notes factory
    m_pat_notes, protected_ids = extract_notes(left_s,RegexPatterns.all()['note'],RegexPatterns.all()['preamble note'],RegexPatterns.Notes.pattern_note_only,protected_ids)

    # studios factory
    m_sound_affiliations_and_parenthesis, protected_ids = extract_new_sound(left_s,
                                                                            RegexPatterns.all()['new_sound_frame'],
                                                                            RegexPatterns.all()[
                                                                                'new_sound_frame_parenthesis'],
                                                                            protected_ids)
    m_sound_final, protected_ids = extract_sound(left_s, RegexPatterns.all()['studio'],
                                                                 RegexPatterns.all()['sound director'], protected_ids)
    #muscial_directors factory
    m_music_director = extract_musical_directors(left_s,RegexPatterns.all()['musical director'])



    # simple pairs factory
    m_pairs,protected_ids = extract_pairs(left_s,RegexPatterns.all()['role_pairs'],protected_ids)

    # head factory
    m_head = (left_s.str.extract(RegexPatterns.all()['studio_head'])
              .reset_index(names='row_id')
              .dropna(subset=['head'])).assign(role='head of department',
                                             entity=lambda d: d['head'].astype('string').str.strip())
    # head ready
    m_head['row_id'] = m_head['row_id'].astype('int64')
    m_head_final = m_head[['row_id', 'role', 'entity']]
    m_head_final = ensure_schema_min(m_head_final)

    # parentheses factory
    m_paren_ent, protected_ids = extract_parent_ent(left_s,RegexPatterns.all()['entity_paren'],protected_ids)
    # print("Jeste m_paren_ent po wyjsciu z funkcji: \n",m_paren_ent)

    #producers factory
    m_prod_roles = extract_prod(left_s,RegexPatterns.all()['studio_name_producer'])
    m_prod_roles = split_entity_col(m_prod_roles,'entity')
    left_s = left_s.map(norm_entity)
    # print("Jestem m prod roles: \n",m_prod_roles)

    #all written factory
    m_written_final = extract_hand_written(left_s,RegexPatterns.all()['written by'])
    m_written_final = ensure_schema_min(m_written_final)
    # print("Jestem m_written_final: \n",m_written_final)

    # foreign language movies factory
    m_foreign = extract_foreign_lg(left_s,RegexPatterns.all()['foreign movie'])

    # sanity check
    protected_ids_for_generic = set().union(
        m_sound_affiliations_and_parenthesis['row_id'].unique(),
        m_by_paren['row_id'].unique(),
        m_pat_notes['row_id'].unique(),
        m_prod_paren['row_id'].unique(),
        m_foreign['row_id'].unique(),
        m_pairs['row_id'].unique(),
        m_written_final['row_id'].unique(),
        m_music_director['row_id'].unique(),
        m_sound_final['row_id'].unique(),
        m_head_final['row_id'].unique(),
        m_paren_ent['row_id'].unique(),
        m_prod_roles['row_id'].unique(),

    )
    print(protected_ids)
    # generic factory
    left_s_generic = left_s.loc[~left_s.index.isin(protected_ids_for_generic)]
    m_generic = left_s_generic.map(split_keep_protected).explode().reset_index().rename(
        columns={'index': 'row_id', 'left': 'entity'}).assign(role=pd.NA)
    m_generic_full = ensure_schema_min(m_generic)
    TRANSFORMED.mkdir(parents=True, exist_ok=True)
    m_generic_full.to_csv(TRANSFORMED / 'm_generic_full.csv')
    # concat because double role per entity
    m_head_written_final = extract_head_written(m_by_paren,m_head_final,m_written_final)

    frames_dictionary = {
        "new_frame": m_sound_affiliations_and_parenthesis,
        "m_paren_ent": m_paren_ent,
        "music_director": m_music_director,
        "m_pairs": m_pairs,
        "m_prod_parenthesis": m_prod_paren,
        "m_prod_roles": m_prod_roles,
        "m_head_written_final": m_head_written_final,
        "m_sound_final": m_sound_final,
        "foreign": m_foreign,
    }
    for key, frame in frames_dictionary.items():
        print(key," :\n",frame)
    res = audit_overlaps(frames_dictionary)
    for name, df in res.items():
        print("\n====", name, "====")
        print(df)
    print(m_pat_notes)
    m_generic_full,pri_all = build_pri_all(base,frames_dictionary,m_pat_notes,m_generic_full)

    pri_all['entity'] = pri_all['entity'].apply(
        lambda x: x[0] if isinstance(x, (list, tuple)) and len(x) > 0 else x)
    pri_all['entity'] = pri_all['entity'].astype('string').map(norm_entity)
    pri_all['role'] = pri_all['role'].astype('string')
    pri_all.loc[pri_all['role'].notna(), 'role'] = pri_all.loc[pri_all['role'].notna(), 'role'].map(norm_role)

    pri_all = pri_all.drop_duplicates(subset=['row_id', 'entity', 'role'], keep='first')

    pri_all['entity'] = pri_all['entity'].map(norm_entity)
    pri_all['row_id'] = pri_all['row_id'].astype('int64')
    m_generic_full['row_id'] = m_generic_full['row_id'].astype('int64')

    existing_ids = set(pri_all['row_id'])
    m_generic_filtered = m_generic_full.loc[~m_generic_full['row_id'].isin(existing_ids)]
    frames = [pri_all, m_generic_filtered]
    frames = [f for f in frames if f is not None and not f.empty]
    finalists = (
        pd.concat(frames, ignore_index=True)
        if frames else pd.DataFrame(columns=['row_id', 'entity', 'role'])
    )

    out = base.merge(
        finalists,
        on='row_id'
    )

    if 'person_fallback' in out.columns:
        out['entity'] = out['entity'].combine_first(out['person_fallback'])

    cat_up = out['category'].astype('string').str.upper()
    left_s = out['left'].astype('string')

    is_writing = cat_up.str.startswith('WRITING')
    out.loc[out['role'].isna() & is_writing, 'role'] = 'screenplay'

    has_scoring = cat_up.str.contains(r'\bSCORING\b', na=False) | left_s.str.contains(r'(?i)\bScoring\b', na=False)
    has_score = cat_up.str.contains(r'\bSCORE\b', na=False) | left_s.str.contains(r'(?i)\bScore\b', na=False)
    mask_empty = out['role'].isna()
    out.loc[mask_empty & has_scoring, 'role'] = 'scoring'
    mask_empty = out['role'].isna()
    out.loc[mask_empty & has_score, 'role'] = 'score'

    if 'entity' not in out.columns: out['entity'] = pd.NA
    if 'role'   not in out.columns: out['role']   = pd.NA

    out['_no_role'] = out['role'].isna()
    out = (out.sort_values(['row_id', '_no_role', 'entity'])
           .drop(columns='_no_role'))

    return out



from itertools import combinations
import pandas as pd

def ensure_schema_min(df):
    g = df.copy()
    for c in ['row_id','entity','role','note','affiliation','person']:
        if c not in g.columns:
            g[c] = pd.NA
    return g[['row_id','entity','role','note','affiliation','person']]

def overlap_matrix(dfs: dict[str, pd.DataFrame], key='row_id') -> pd.DataFrame:
    names = list(dfs.keys())
    sets = {k: set(dfs[k][key].dropna().unique()) for k in names}
    data = [[len(sets[a] & sets[b]) for b in names] for a in names]
    return pd.DataFrame(data, index=names, columns=names)

def overlap_matrix_entity(dfs: dict[str, pd.DataFrame],
                          key_cols=('row_id','entity')) -> pd.DataFrame:
    names = list(dfs.keys()); sets = {}
    for k, df in dfs.items():
        if not set(key_cols) <= set(df.columns):
            sets[k] = set(); continue
        tmp = (df[list(key_cols)].dropna()
               .assign(**{key_cols[1]: df[key_cols[1]].astype('string').str.strip().str.lower()}))
        sets[k] = set(map(tuple, tmp.drop_duplicates().itertuples(index=False, name=None)))
    data = [[len(sets[a] & sets[b]) for b in names] for a in names]
    return pd.DataFrame(data, index=names, columns=names)

def audit_overlaps(
    dfs: dict[str, pd.DataFrame],
    key: str = "row_id",
    entity_col: str = "entity",
) -> dict[str, pd.DataFrame]:

    # macierze globalne
    m_row = overlap_matrix(dfs, key=key)
    m_ent = overlap_matrix_entity(dfs, key_cols=(key, entity_col))

    # per-frame counts
    per_frame_rows = []
    for name, df in dfs.items():
        n_total = len(df)
        n_with_key = len(df) if key in df.columns else 0
        n_with_entity = len(df) if entity_col in df.columns else 0
        per_frame_rows.append({
            "frame": name,
            "rows_total": n_total,
            f"rows_with_{key}": n_with_key,
            f"rows_with_{entity_col}": n_with_entity,
        })
    per_frame_df = pd.DataFrame(per_frame_rows).sort_values("frame")

    # zlepienie wszystkiego w jedną tabelę “długą”
    frames = []
    for name, df in dfs.items():
        if key not in df.columns:
            continue
        cols = [key]
        if entity_col in df.columns:
            cols.append(entity_col)
        if "role" in df.columns:
            cols.append("role")
        if "note" in df.columns:
            cols.append("note")

        g = df[cols].copy()
        g["source"] = name
        if entity_col in g.columns:
            g["entity_norm"] = (
                g[entity_col]
                .astype("string")
                .str.strip()
                .str.lower()
            )
        else:
            g["entity_norm"] = pd.NA
        frames.append(g)

    if not frames:
        # brak sensownych ramek
        summary = pd.DataFrame(
            [{"metric": "total_rows_all_frames", "value": 0},
             {"metric": "unique_keys_all_frames", "value": 0}]
        )
        return {
            "summary": summary,
            "per_frame": per_frame_df,
            "matrix_row_id": m_row,
            "matrix_entity": m_ent,
            "pairwise_overlaps": pd.DataFrame(),
            "repeated_keys": pd.DataFrame(),
            "repeated_key_entity": pd.DataFrame(),
        }

    all_df = pd.concat(frames, ignore_index=True)

    # repeated by KEY – dokładnie które row_id występują w > 1 source
    g_key = (
        all_df.groupby(key, dropna=False)
        .agg(
            sources=("source", lambda s: tuple(sorted(set(s)))),
            n_sources=("source", lambda s: len(set(s))),
        )
        .reset_index()
    )
    repeated_keys = g_key[g_key["n_sources"] > 1].sort_values([ "n_sources", key ], ascending=[False, True])

    # możemy też dołączyć “wypłaszczenie”
    repeated_key_details = all_df.merge(
        repeated_keys[[key, "n_sources"]],
        on=key,
        how="inner"
    ).sort_values([key, "source"])

    # repeated by (KEY, ENTITY)
    ent_df = all_df.dropna(subset=["entity_norm"]).copy()
    grouped = (
        ent_df.groupby([key, "entity_norm"], dropna=False)
        .agg(
            sources=("source", lambda s: tuple(sorted(set(s)))),
            roles=("role", lambda s: tuple(sorted(set(x for x in s.astype("string") if pd.notna(x))))),
            entity_show=(entity_col, "first"),
            sample_note=("note", "first"),
        )
        .reset_index()
    )
    grouped["n_sources"] = grouped["sources"].apply(len)
    grouped["n_roles"] = grouped["roles"].apply(len)

    multi_hits = grouped[grouped["n_sources"] > 1].sort_values(
        ["n_sources", key], ascending=[False, True]
    )
    conflicts = multi_hits[multi_hits["n_roles"] > 1].copy()

    # pairwise overlaps – ile A ma wspólnych z B + ile ma wspólnych (key,entity)
    pairwise_rows = []
    names = list(dfs.keys())
    for a, b in combinations(names, 2):
        df_a = dfs[a]
        df_b = dfs[b]

        # key overlap
        if key in df_a.columns and key in df_b.columns:
            set_a = set(df_a[key].dropna())
            set_b = set(df_b[key].dropna())
            key_overlap = len(set_a & set_b)
        else:
            key_overlap = 0

        # (key, entity) overlap
        if entity_col in df_a.columns and entity_col in df_b.columns and key in df_a.columns and key in df_b.columns:
            a_ent = (
                df_a[[key, entity_col]]
                .dropna(subset=[key])
                .assign(_ent=lambda x: x[entity_col].astype("string").str.strip().str.lower())
            )
            b_ent = (
                df_b[[key, entity_col]]
                .dropna(subset=[key])
                .assign(_ent=lambda x: x[entity_col].astype("string").str.strip().str.lower())
            )
            set_a_ent = set(zip(a_ent[key], a_ent["_ent"]))
            set_b_ent = set(zip(b_ent[key], b_ent["_ent"]))
            ent_overlap = len(set_a_ent & set_b_ent)
        else:
            ent_overlap = 0

        pairwise_rows.append({
            "frame_a": a,
            "frame_b": b,
            "key_overlap": key_overlap,
            "key_overlap_pct_of_a": key_overlap / len(df_a) if len(df_a) else 0,
            "key_overlap_pct_of_b": key_overlap / len(df_b) if len(df_b) else 0,
            "key_entity_overlap": ent_overlap,
        })

    pairwise_df = pd.DataFrame(pairwise_rows).sort_values(
        ["key_overlap", "key_entity_overlap"], ascending=[False, False]
    )

    # summary
    total_rows_all = sum(len(df) for df in dfs.values())
    all_keys = set()
    for name, df in dfs.items():
        if key in df.columns:
            all_keys.update(df[key].dropna().tolist())
    summary = pd.DataFrame(
        [
            {"metric": "total_rows_all_frames", "value": total_rows_all},
            {"metric": f"unique_{key}_all_frames", "value": len(all_keys)},
            {"metric": "frames_count", "value": len(dfs)},
            {"metric": "rows_with_duplicate_key_across_frames", "value": len(repeated_keys)},
        ]
    )

    return {
        "matrix_row_id": m_row,
        "matrix_entity": m_ent,

        # nowe / rozbudowane
        "summary": summary,
        "per_frame": per_frame_df,
        "pairwise_overlaps": pairwise_df,

        # dokładne powtórki
        "repeated_keys": repeated_keys,
        "repeated_key_details": repeated_key_details,

        # z poziomu entity
        "multi_hits": multi_hits[[
            key, "entity_show", "roles", "sources", "sample_note", "n_sources"
        ]],
        "conflicts": conflicts[[
            key, "entity_show", "roles", "sources", "sample_note", "n_sources"
        ]],
    }

def subtract_generic_by_priority(m_generic_full, pri_all, norm):
    if m_generic_full.empty or pri_all.empty:
        return m_generic_full
    pa = (pri_all[['row_id','entity']].dropna()
            .assign(entity_norm=lambda d: d['entity'].astype('string').map(norm))
            .drop_duplicates(['row_id','entity_norm']))
    mg = (m_generic_full
            .assign(entity_norm=lambda d: d['entity'].astype('string').map(norm))
            .merge(pa[['row_id','entity_norm']], on=['row_id','entity_norm'], how='left', indicator=True))
    return mg.loc[mg['_merge']=='left_only'].drop(columns=['_merge','entity_norm'])




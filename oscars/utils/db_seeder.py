import sqlite3
from oscars.utils.db_sqlite3 import create_schema
import pandas as pd

def export_to_sqlite(df_roles: pd.DataFrame, db_path: str):
    conn = sqlite3.connect(db_path)
    create_schema(conn)
    cur = conn.cursor()

    # --- CEREMONIES ---
    ceremonies = (
        df_roles[['year']]
        .dropna()
        .drop_duplicates()
        .sort_values('year')
        .reset_index(drop=True)
    )
    ceremonies['ceremony_id'] = ceremonies.index + 1

    cur.executemany(
        "INSERT OR IGNORE INTO ceremonies (ceremony_id, year) VALUES (?, ?);",
        ceremonies[['ceremony_id', 'year']].itertuples(index=False, name=None)
    )

    year_to_ceremony = dict(
        ceremonies[['year', 'ceremony_id']].itertuples(index=False, name=None)
    )

    # --- CATEGORIES ---
    categories = (
        df_roles[['category']]
        .dropna()
        .drop_duplicates()
        .sort_values('category')
        .reset_index(drop=True)
        .rename(columns={'category': 'name'})
    )
    categories['category_id'] = categories.index + 1

    cur.executemany(
        "INSERT OR IGNORE INTO categories (category_id, name) VALUES (?, ?);",
        categories[['category_id', 'name']].itertuples(index=False, name=None)
    )

    cat_to_id = dict(
        categories[['name', 'category_id']].itertuples(index=False, name=None)
    )

    # --- FILMS ---
    films = (
        df_roles[['title','year']]
        .dropna(subset=['title'])
        .drop_duplicates()
        .sort_values(['title','year'])
        .reset_index(drop=True)
    )
    films['film_id'] = films.index + 1

    cur.executemany(
        "INSERT OR IGNORE INTO films (film_id, title, year) VALUES (?, ?, ?);",
        films[['film_id','title','year']].itertuples(index=False, name=None)
    )

    film_key = {
        (t.title, t.year): t.film_id
        for t in films[['title','year','film_id']].itertuples(index=False)
    }

    # --- ENTITIES ---
    ent_cols = ['entity', 'entity_type', 'gender']
    for c in ent_cols:
        if c not in df_roles.columns:
            df_roles[c] = None

    entities = (
        df_roles[['entity','entity_type','gender']]
        .dropna(subset=['entity'])
        .drop_duplicates()
        .reset_index(drop=True)
    )
    entities['entity_id'] = entities.index + 1

    cur.executemany(
        "INSERT OR IGNORE INTO entities (entity_id, name, entity_type, gender) VALUES (?, ?, ?, ?);",
        entities[['entity_id','entity','entity_type','gender']].itertuples(index=False, name=None)
    )

    ent_key = {
        (t.entity, t.entity_type): t.entity_id
        for t in entities[['entity','entity_type','entity_id']].itertuples(index=False)
    }

    # --- NOMINATIONS ---
    nom_base = (
        df_roles[['row_id','year','category','title','is_winner','role','note']]
        .drop_duplicates(subset=['row_id'])
        .rename(columns={'row_id': 'nomination_id'})
        .reset_index(drop=True)
    )

    rows_nom = []
    for _, r in nom_base.iterrows():
        nomination_id = int(r['nomination_id'])
        year = int(r['year'])
        category = str(r['category'])

        ceremony_id = year_to_ceremony[year]
        category_id = cat_to_id[category]

        film_id = film_key.get((r['title'], year)) if pd.notna(r['title']) else None
        is_winner = int(bool(r.get('is_winner')))

        rows_nom.append(
            (nomination_id, ceremony_id, category_id, film_id, is_winner, r['role'], r['note'])
        )

    cur.executemany("""
        INSERT OR REPLACE INTO nominations
        (nomination_id, ceremony_id, category_id, film_id, is_winner, role, note)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, rows_nom)

    # --- ROLES ---
    role_cols = ['row_id','entity','entity_type','role_function','role_subtype']
    for c in role_cols:
        if c not in df_roles.columns:
            df_roles[c] = None

    roles_df = df_roles[role_cols].dropna(subset=['entity'])

    rows_roles = []
    for _, r in roles_df.iterrows():
        nomination_id = int(r['row_id'])
        entity_id = ent_key.get((r['entity'], r['entity_type']))

        if entity_id is None:
            continue

        rows_roles.append((
            nomination_id,
            entity_id,
            r.get('role_function'),
            r.get('role_subtype')
        ))

    cur.executemany("""
        INSERT INTO roles
        (nomination_id, entity_id, role_function, role_subtype)
        VALUES (?, ?, ?, ?);
    """, rows_roles)

    conn.commit()
    conn.close()

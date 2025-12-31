from __future__ import annotations
from pathlib import Path
import argparse
import pandas as pd
import numpy as np
def ensure_dir(p):
    p = Path(p)
    p.mkdir(parents=True, exist_ok=True)
    return p

DEPT_LABELS = ["Acting","Directing","Writing","Cinematography","Editing","Production design","Music"]

def department_from_row(role:str, role_function:str) -> str:
    r = (role or "").lower()
    f = (role_function or "").lower()
    if f == "acting":       return "Acting"
    if f == "directing":    return "Directing"
    if f == "writing":      return "Writing"
    if f == "music":        return "Music"
    # craft – rozbijamy:
    if r in ("cinematographer",):                 return "Cinematography"
    if r in ("editor",):                          return "Editing"
    if r in ("production designer","art director","set decorator","interior decorator"):
        return "Production design"
    return None

def acting_winners_by_decade_pivot(df_roles: pd.DataFrame) -> pd.DataFrame:
    """Pivot: dekada x [male, female] – zwycięzcy w rolach aktorskich."""
    people = make_people_scope(df_roles)
    acting_winners = (
        people
        .query("(role_function == 'acting') and is_winner == 1 and gender in ['male','female']")
        .assign(decade=lambda d: (d['year'] // 10) * 10)
    )

    pivot = (
        acting_winners
        .groupby(['decade','gender']).size()
        .unstack('gender')
        .reindex(columns=['male','female'])
        .fillna(0).astype(int)
        .sort_index()
    )
    # ładne etykiety dekad
    pivot.index = pivot.index.map(lambda y: f"{int(y)}s")
    pivot.columns = ['Male', 'Female']
    return pivot

def load_df_roles(path) -> pd.DataFrame:
    return pd.read_csv(path)

def make_people_scope(df_roles: pd.DataFrame) -> pd.DataFrame:
    """
    Filtr: tylko encje uznane za osoby i brane do analiz.
    Dodatkowo tworzy nom_key = unikalny klucz nominacji (rok|kategoria|tytuł|osoba).
    """
    indexes =  df_roles['row_id']
    people = df_roles.query("include_role == True and is_person == True").copy()

    # unifikacja kategorii

    people['category'] = people.get('category')

    # bezpieczny tytuł
    title = people.get('title')
    if title is None:
        title = ''
    people['__title__'] = pd.Series(title, index=indexes, dtype='string').astype(str).str.strip().str.lower()

    # unikalny klucz nominacji: rok + kategoria + tytuł + osoba
    people['nom_key'] = (
        people['row_id'].astype(str) + '|' +
        people['category'] + '|' +
        people['role'] + '|' +
        people['entity'].astype(str).str.strip().str.lower()
    )

    # porządki pośrednich kolumn
    people = people.drop(columns=['__cat__', '__title__'], errors='ignore')
    return people


def women_metrics_by_year(people: pd.DataFrame) -> pd.DataFrame:
    """
    Zwraca ramkę z indeksami = lata i kolumnami:
      - female_nominees
      - female_winners
      - female_winner_share  (w %)
    Liczenie na zduplikowanych nominacjach jest unikane przez użycie 'nom_key'.
    """

    nom_u = people[['year', 'gender', 'nom_key']].drop_duplicates('nom_key')

    # Zwycięzcy – też unikat po kluczu nominacji
    win_u = people.loc[people['is_winner'] == 1, ['year', 'gender', 'nom_key']].drop_duplicates('nom_key')

    # Agregacje bez deprecated apply:
    female_nominees = nom_u.loc[nom_u['gender'] == 'female'].groupby('year').size()
    female_winners  = win_u.loc[win_u['gender'] == 'female'].groupby('year').size()

    total_winners   = win_u.groupby('year').size()

    # Zbierz lata (pełny zakres obecny w danych)
    all_years = pd.Index(sorted(set(people['year'].dropna().astype(int).tolist())), name='year')
    out = pd.DataFrame(index=all_years)
    out['female_nominees'] = female_nominees.reindex(all_years, fill_value=0)
    out['female_winners']  = female_winners.reindex(all_years,  fill_value=0)
    out['total_winners']   = total_winners.reindex(all_years,   fill_value=0)

    # udział w %
    with np.errstate(divide='ignore', invalid='ignore'):
        share = (out['female_winners'] / out['total_winners']) * 100.0
    out['female_winner_share'] = share.fillna(0)

    # niepotrzebna kolumna pomocnicza
    out = out.drop(columns=['total_winners'])
    return out

def to_decade(y: int) -> int:
    return int(y) // 10 * 10

def parse_args(default_in, default_out):
    ap = argparse.ArgumentParser()
    ap.add_argument("--in",  dest="inp",     default=str(default_in))
    ap.add_argument("--out", dest="out_dir", default=str(default_out))
    args = ap.parse_args([])
    out_dir = ensure_dir(args.out_dir)
    return args.inp, out_dir

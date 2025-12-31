from __future__ import annotations
import os, pandas as pd, matplotlib.pyplot as plt
from analitics._helpers import load_df_roles, make_people_scope, parse_args

DEFAULT_IN  = "../../transformed/golden_version.csv"
DEFAULT_OUT = "../../transformed/figures_acting"

def run_from_df(df_roles: pd.DataFrame, out_dir: str = DEFAULT_OUT):
    os.makedirs(out_dir, exist_ok=True)
    people = make_people_scope(df_roles)

    acting   = people.query("role_function == 'acting'").copy()
    acting_u = acting[['entity','gender','is_winner','nom_key']].drop_duplicates()

    # wins
    wins = (acting_u.query("is_winner == 1")
            .groupby('entity').size().sort_values(ascending=False))
    top_wins = wins.head(20)

    plt.figure(figsize=(8,8))
    top_wins.iloc[::-1].plot(kind='barh')
    plt.title('Top aktorzy/aktorki – WYGRANE (ALL-TIME)')
    plt.xlabel('Liczba wygranych'); plt.ylabel('Osoba')
    plt.tight_layout()
    p1 = os.path.join(out_dir, "acting_top_wins.png")
    plt.savefig(p1, dpi=150); plt.close()
    top_wins.to_csv(os.path.join(out_dir, "acting_top_wins.csv"), header=['wins'])

    # nominations
    noms = (acting_u.groupby('entity').size().sort_values(ascending=False))
    top_noms = noms.head(20)

    plt.figure(figsize=(8,8))
    top_noms.iloc[::-1].plot(kind='barh')
    plt.title('Top aktorzy/aktorki – NOMINACJE (ALL-TIME)')
    plt.xlabel('Liczba nominacji'); plt.ylabel('Osoba')
    plt.tight_layout()
    p2 = os.path.join(out_dir, "acting_top_noms.png")
    plt.savefig(p2, dpi=150); plt.close()
    top_noms.to_csv(os.path.join(out_dir, "acting_top_noms.csv"), header=['nominations'])

    return {"png": [p1, p2]}

def main():
    inp, out_dir = parse_args(DEFAULT_IN, DEFAULT_OUT)
    df_roles = load_df_roles(inp)
    run_from_df(df_roles, out_dir)

if __name__ == "__main__":
    main()

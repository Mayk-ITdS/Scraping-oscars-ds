import csv
from pathlib import Path
import cProfile, pstats, io
import analysis
from oscars.parsing.NamesBuffer import NamesBuffer
from oscars.scraping.extract_from_text import extract_title_and_left,extract_roles_by_person
from oscars.parsing.GenderResolver import GenderResolver
from oscars.scraping.extract import flattened
from oscars.utils.db_seeder import export_to_sqlite
from oscars.utils.queries_tests import ask_my_base

ROOT = Path(__file__).resolve().parents[1]
TRANSFORMED = ROOT / "transformed"
FIG_GENDER = TRANSFORMED / "figures_gender"
FIG_ACTING = TRANSFORMED / "figures_acting"
cPROFILER_STATS = TRANSFORMED / "cProfiler_stats.prof"
ANALYSIS = ROOT /  "analysis"
for d in (TRANSFORMED, FIG_GENDER, FIG_ACTING,cPROFILER_STATS):
    d.mkdir(parents=True, exist_ok=True)

def main():
    df = flattened()
    df = extract_title_and_left(df)
    df = extract_roles_by_person(df)
    print("after extract roles: \n",df[df['row_id'].isin([4314,4376])])
    df_roles = GenderResolver.harmonize_roles(df, role_col="role", category_col="category")
    print("after harmonize_roles: \n",df_roles[df_roles['row_id'].isin([4314,4376])])
    unmatched = df_roles[(df_roles["role"].isna()) | (df_roles["role"] == "")]
    unmatched = unmatched.copy()
    unmatched["category_repr"] = unmatched["category"].apply(lambda x: repr(str(x)))
    print("ILE:", len(unmatched))
    print(unmatched[["row_id", "entity",'role', "category", "category_repr"]].drop_duplicates().sort_values("category"))
    duplicates = df_roles.duplicated(subset=['title',"row_id", "entity", "category", "role",'role_function','affiliation','person'])
    for dup in duplicates:
        if dup == 'True':
            print(dup)

    df_roles['entity'] = df_roles['entity'].map(NamesBuffer.normalize_entity)

    analysis.drafts.visualize(df_roles.copy(), ANALYSIS)
    export_to_sqlite(df_roles, TRANSFORMED / "role_oscars_gold.db")
    ask_my_base()
    df_roles.to_csv(TRANSFORMED / "final_oscars_data.csv", quoting=csv.QUOTE_ALL,index=False)


if __name__ == "__main__":
    pr = cProfile.Profile()
    pr.enable()
    main()
    pr.disable()

    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).strip_dirs().sort_stats("cumtime")
    ps.print_stats(40)  # top 40 wpisów
    print(s.getvalue())

    pr.dump_stats("profile.prof")
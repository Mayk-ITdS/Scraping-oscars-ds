import pandas as pd
import re
from pathlib import Path
import sys
def classify_difficulty(text: str) -> str:
    if pd.isna(text):
        text = ""
    else:
        text = str(text)

    text = re.sub(r'''\s+[-–—]\s+"\s*.*\s*"''', '', text)
    lowered = text.lower()
    # --- podstawowe flagi separatorów ---
    has_semicolon = ";" in text
    has_colon = ":" in text
    has_and_word = bool(re.search(r"\band\b", lowered))
    has_ampersand = bool(re.search(r"\s&\s", text))
    # treat any & as conjunction too, but to be safe:
    if "&" in text and not has_ampersand:
        has_ampersand = True
    # dash, note-like
    has_dash = any(x in text for x in [" - ", " – ", " — "])
    has_note_keyword = bool(re.search(
        r"\b(for|in recognition|in appreciation|with thanks|presented to|whose|who)\b",
        lowered
    ))
    # special cases: note-ish, film-left-then-dash
    if has_note_keyword or has_dash:
        return "special"
    # liczba typów separatorów
    sep_types = [
        has_semicolon,
        has_colon,
        has_and_word,
        has_ampersand,
    ]
    n_types = sum(sep_types)
    # easy: brak separatorów lub tylko jedno 'źródło'
    if n_types <= 1:
        return "easy"

    # medium / upper_medium / hard
    has_conj = has_and_word or has_ampersand
    has_punct = has_semicolon or has_colon

    if n_types == 2:
        # jeśli mieszamy spójniki i interpunkcję, to już jest hard
        if has_conj and has_punct:
            return "hard"
        else:
            return "medium"
    # n_types >= 3
    if has_conj and has_punct:
        return "hard"
    else:
        return "upper_medium"


def generate_raw_report(df_series,path, output_path=None,
                        max_object_examples=20,
                        random_state=42,
                        difficulty_csv_path=None):
    path = Path(path)
    df = df_series.copy()
    lines = []

    def add(section_title, content_lines=None):
        lines.append(section_title)
        if content_lines:
            lines.extend(content_lines)
        lines.append("")

    # header
    n_rows, n_cols = df.shape
    add("=== RAW OSCARS DATA REPORT ===", [
        f"Source file: {path.resolve()}",
        f"Number of rows (raw nominations): {n_rows:,}",
        f"Number of columns: {n_cols}",
        "Columns:",
        "  " + ", ".join(df.columns)
    ])

    # [1] YEAR AND CEREMONY COVERAGE
    if 'year' in df.columns:
        years = df['year'].dropna()
        try:
            years = years.astype(int)
        except Exception:
            pass
        if not years.empty:
            decade = (years // 10) * 10
            year_counts = years.value_counts().sort_index()
            dec_counts = decade.value_counts().sort_index()
            year_lines = [
                f"Year range: {int(years.min())}–{int(years.max())}",
                f"Number of distinct ceremony years: {years.nunique()}",
                "",
                "Top 10 years by number of nominations:"
            ]

            for y, c in year_counts.head(10).items():
                year_lines.append(f"  {y}: {c}")
            year_lines.append("")
            year_lines.append("Nominations per decade:")
            for d, c in dec_counts.items():
                year_lines.append(f"  {d}s: {c}")
            add("[1] YEAR AND CEREMONY COVERAGE", year_lines)

    # [2] CATEGORIES
    if 'category' in df.columns:
        cat = df['category'].astype(str)
        vc = cat.value_counts()
        cat_lines = [
            f"Number of distinct categories: {vc.shape[0]}",
            "",
            "Top 15 categories by number of nominations:"
        ]
        for name, c in vc.head(15).items():
            cat_lines.append(f"  {name}: {c}")
        add("[2] CATEGORIES", cat_lines)

    # [3] TITLES (optional)
    if 'title' in df.columns:
        titles = df['title'].astype(str)
        uniq_titles = titles.nunique()
        title_lines = [
            f"Number of distinct film titles: {uniq_titles}",
            "Top 15 most frequently nominated titles:"
        ]
        vc_t = titles.value_counts().head(15)
        for t, c in vc_t.items():
            title_lines.append(f"  {t}: {c}")
        add("[3] TITLES", title_lines)

    # [4] COMPLETENESS / MISSINGNESS
    miss = df.isna().mean().sort_values(ascending=False)
    miss_lines = ["Missing values per column (share of rows):"]
    for col, frac in miss.items():
        miss_lines.append(f"  {col}: {frac:.3%}")
    add("[4] COMPLETENESS / MISSINGNESS", miss_lines)

    # [5] OBJECT COLUMN: HETEROGENEITY
    if 'object' in df.columns:
        obj = df['object'].astype(str)
        lengths = obj.str.len()
        obj_lines = [
            f"Number of non-null object rows: {obj.notna().sum():,}",
            f"Object length (characters): min={lengths.min()}, "
            f"max={lengths.max()}, mean={lengths.mean():.1f}, "
            f"median={lengths.median():.1f}",
            "",
        ]
        patterns = {
            "contains ';'": obj.str.contains(";", na=False),
            "contains ' and '": obj.str.contains(r"\sand\s", na=False),
            "contains ' & '": obj.str.contains(r"\s&\s", na=False),
            "contains 'Visual Effects'": obj.str.contains("Visual Effects", case=False, na=False),
            "contains 'Music and Lyrics'": obj.str.contains("Music and Lyrics", case=False, na=False),
            "contains 'Government'": obj.str.contains("Government", case=False, na=False),
            "contains 'Department'": obj.str.contains("Department", case=False, na=False),
            "contains 'not awarded' or 'no award'":
                obj.str.contains("not awarded|no award", case=False, na=False),
        }
        obj_lines.append("Heuristic pattern counts in the object column:")
        for label, mask in patterns.items():
            obj_lines.append(f"  {label}: {mask.sum()}")

        obj_lines.append("")
        obj_lines.append(f"Random sample of up to {max_object_examples} raw object rows:")
        sample = obj.sample(n=min(max_object_examples, len(obj)), random_state=random_state)
        for idx, txt in sample.items():
            short = (txt[:50] + "…") if len(txt) > 50 else txt
            obj_lines.append(f"  [row {idx}] {short}")

        add("[5] OBJECT COLUMN: HETEROGENEITY", obj_lines)

        # [7] DIFFICULTY CLASSES – tylko jeśli mamy object
        diff_series = obj.map(classify_difficulty)
        df['difficulty_level'] = diff_series

        vc_diff = diff_series.value_counts()
        diff_lines = ["Row difficulty classes (based on separator patterns):"]
        total = len(diff_series)
        for level, c in vc_diff.items():
            diff_lines.append(f"  {level}: {c} ({c/total:.1%})")

        # Średnie długości per klasa – fajne do opisu w pracy
        lengths_by_diff = lengths.groupby(diff_series).agg(['count', 'mean', 'min', 'max'])
        diff_lines.append("")
        diff_lines.append("Object length stats per difficulty level:")
        for level, row in lengths_by_diff.iterrows():
            diff_lines.append(
                f"  {level}: n={int(row['count'])}, "
                f"mean_len={row['mean']:.1f}, "
                f"min={int(row['min'])}, max={int(row['max'])}"
            )

        add("[7] ROW DIFFICULTY CLASSES", diff_lines)

        # opcjonalnie zapis do osobnego CSV (np. tylko hard + special)
        if difficulty_csv_path:
            difficulty_csv_path = Path(difficulty_csv_path)
            df.to_csv(difficulty_csv_path, index=False)

    # [6] DUPLICATES (RAW LEVEL)
    dup_cols = [c for c in ['year', 'category', 'object','is_winner'] if c in df.columns]
    if dup_cols:
        dup_mask = df.duplicated(subset=dup_cols, keep=False)
        n_dup = dup_mask.sum()
        dup_lines = [
            f"Number of duplicated rows when grouping by {dup_cols}: {n_dup}",
        ]
        if n_dup > 0:
            dup_lines.append("Example duplicated combinations (up to 10):")
            ex = (
                df.loc[dup_mask, dup_cols]
                .drop_duplicates()
                .head(10)
            )
            for _, row in ex.iterrows():
                desc = ", ".join(f"{c}={row[c]}" for c in dup_cols)
                dup_lines.append(f"  {desc}")
        add("[6] DUPLICATES (RAW LEVEL)", dup_lines)

    report = "\n".join(lines)
    if output_path:
        output_path = Path(output_path)
        output_path.write_text(report, encoding="utf-8")



    return report





from pathlib import Path
import pandas as pd
from matplotlib import pyplot as plt, rcParams
import seaborn as sns
from matplotlib.patches import Rectangle
import matplotlib.colors as mcolors
from matplotlib.ticker import MaxNLocator
import numpy as np

def visualize(df_,path):

    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    rcParams['figure.facecolor'] = '#020617'   # tlo całej figury
    rcParams['axes.facecolor']   = '#020617'   # tlo osi
    rcParams['axes.edgecolor']   = '#334155'
    rcParams['axes.labelcolor']  = '#e5e7eb'
    rcParams['xtick.color']      = '#e5e7eb'
    rcParams['ytick.color']      = '#e5e7eb'
    rcParams['text.color']       = '#e5e7eb'
    rcParams['font.family']      = 'DejaVu Sans'
    rcParams['axes.titleweight'] = 'bold'
    rcParams['axes.titlesize']   = 14
    rcParams['axes.labelsize']   = 11

    df_persons = df_.loc[df_['is_person']].copy()
    top_20_categories = df_persons['category'].value_counts().head(20).index
    df_persons_categories_top_20 = df_persons.loc[df_persons['category'].isin(top_20_categories)].copy()

    # handles, labels = ax.get_legend_handles_labels()
    oskar_cat_gender_crosstab = pd.crosstab(df_persons_categories_top_20['category'], df_persons_categories_top_20['gender'])
    plt.figure(figsize=(24, 18))
    sns.heatmap(oskar_cat_gender_crosstab, annot=True, fmt='d', cmap='YlGnBu', linewidths=.5)
    plt.title('Nominations per category and gender', fontsize=16)
    plt.xlabel('category', fontsize=12)
    plt.ylabel('gender', fontsize=12)
    plt.tight_layout()
    plt.savefig(path / 'figures_gender' / "category_vs_gender.png", dpi=300)
    plt.show(block=False)
    plt.pause(0.1)
    plt.close()

    YEAR_COL = 'year'

    df_persons_categories_top_20[YEAR_COL] = df_persons_categories_top_20[YEAR_COL].astype(int)

    df_persons_categories_top_20['decade'] = (df_persons_categories_top_20[YEAR_COL] // 10) * 10
    df_persons_categories_top_20['decade_label'] = df_persons_categories_top_20['decade'].astype(str) + '`s'

    acting_roles = {"actor", "actress"}
    producing_roles = {"film_director", "film_producer", "picture_producer", "producer"}


    acting = df_persons.loc[df_persons["role_function"].isin(acting_roles)].copy()
    producing = df_persons.loc[df_persons["role_function"].isin(producing_roles)].copy()

    act_by_film = (
        acting.groupby(["year", "title"])["entity"]
        .unique()
        .reset_index(name="actors")
    )
    prod_by_film = (
        producing.groupby(["year", "title"])["entity"]
        .unique()
        .reset_index(name="producers")
    )

    # tylko filmy, gdzie jest i acting, i producing
    merged = act_by_film.merge(prod_by_film, on=["year", "title"], how="inner")

    pairs = []
    for _, row in merged.iterrows():
        for a in row["actors"]:
            for p in row["producers"]:
                if a != p:
                    pairs.append((a, p))

    if not pairs:
        print("Brak par actor–producer do policzenia.")
        return

    pairs_df = pd.DataFrame(pairs, columns=["actor", "producer"])

    pair_counts = (
        pairs_df
        .value_counts()
        .reset_index(name="n_films")
    )

    top_pairs = pair_counts.sort_values("n_films", ascending=True).tail(15)

    labels = [
        f"{a}\n& {p}"
        for a, p in zip(top_pairs["actor"], top_pairs["producer"])
    ]

    fig_bar, ax_bar = plt.subplots(figsize=(12, 7))
    ax_bar.barh(range(len(top_pairs)), top_pairs["n_films"])
    ax_bar.set_yticks(range(len(top_pairs)))
    ax_bar.set_yticklabels(labels)
    ax_bar.set_xlabel("Nombre de films (nominations) en commun")
    ax_bar.set_title("Paires acteur–producteur/réalisateur les plus fréquentes")

    # tylko ticki całkowite na osi X
    ax_bar.xaxis.set_major_locator(MaxNLocator(integer=True))
    fig_bar.tight_layout()
    fig_bar.savefig(path / "figures_acting" / "actors_producers_top_pairs.png",
                    dpi=300, bbox_inches="tight")
    plt.show(block=False)
    plt.pause(0.1)
    plt.close()

    top_actors = (
        pair_counts.groupby("actor")["n_films"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .index
    )

    top_producers = (
        pair_counts[pair_counts["actor"].isin(top_actors)]
        .groupby("producer")["n_films"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .index
    )

    matrix = (
        pair_counts[
            pair_counts["actor"].isin(top_actors)
            & pair_counts["producer"].isin(top_producers)
            ]
        .pivot_table(
            index="actor",
            columns="producer",
            values="n_films",
            aggfunc="sum",
            fill_value=0
        )
    )

    fig_hm, ax_hm = plt.subplots(figsize=(11, 7))

    sns.heatmap(
        matrix,
        ax=ax_hm,
        annot=True,
        fmt="d",
        cmap="mako",
        linewidths=0.5,
        linecolor="#020617",
        cbar_kws={"label": "Nombre de films (nominations) en commun"}
    )

    ax_hm.set_xlabel("Producer / director")
    ax_hm.set_ylabel("Actor / actress")
    ax_hm.set_title("Collaboration acteurs–producteurs/réalisateurs (TOP 10 × TOP 10)")

    fig_hm.tight_layout()
    fig_hm.savefig(path / "figures_acting"/ "actors_producers_heatmap.png",
                   dpi=300, bbox_inches="tight")
    plt.show(block=False)
    plt.pause(0.1)
    plt.close(fig_hm)

    ct = pd.crosstab(
        index=df_persons_categories_top_20['category'],
        columns=[df_persons_categories_top_20['decade_label'], df_persons_categories_top_20['gender']]
    )
    tab = pd.crosstab(
        index=df_persons_categories_top_20['decade'],
        columns=df_persons_categories_top_20['category']
    )

    ct = ct.sort_index(axis=1, level=[0, 1])

    ct.columns = [f"{dec}_{gender}" for dec, gender in ct.columns]
    tab = tab.sort_index()

    plt.figure(figsize=(24, 16))
    sns.heatmap(tab, annot=True, fmt='d', cmap='YlGnBu', linewidths=.5)

    plt.title('Nombre de nominés par catégorie et décennie', fontsize=16)
    plt.xlabel('Décennie_genre', fontsize=12)
    plt.ylabel('Catégorie', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(path / 'figures_acting' / 'nominees_par_category_decennia')
    plt.show(block=False)
    plt.pause(0.1)
    plt.close()
    # 🔹 4. Heatmapa
    plt.figure(figsize=(22, 10))
    sns.heatmap(ct, annot=True, fmt='d', cmap='YlGnBu', linewidths=.5)
    plt.title('Nominacje wg kategorii, dekady i płci (jedna macierz)', fontsize=16)
    plt.xlabel('Décennie_genre', fontsize=12)
    plt.ylabel('Kategoria', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(path / 'figures_acting' / 'one_matrix.png')
    plt.show(block=False)
    plt.pause(0.1)
    plt.close()

    category_by_decade = pd.crosstab(index=df_persons_categories_top_20['decade'],columns=df_persons_categories_top_20['category'], normalize='index') * 100

    n_decades = category_by_decade.shape[0]
    n_cols    = category_by_decade.shape[1]

    fig_w = max(10, n_cols * 0.50)
    fig_h = 6

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))

    fig.subplots_adjust(left=0.10, right=0.78, top=0.88, bottom=0.18)

    category_by_decade.plot(kind='bar', stacked=True, colormap='viridis',ax=ax)
    ax.set_title('Part en pourcentage des nominations par catégorie et décennie',fontsize=16)
    ax.set_xlabel('Décennie',labelpad=10)
    ax.set_ylabel('Pourcentage')
    ax.set_xticklabels([f"{int(d)}`s" for d in category_by_decade.index], rotation=0)
    handles, labels = ax.get_legend_handles_labels()
    n_legend_cols = min(len(category_by_decade.columns), 5)
    ax.legend(handles,labels,title="Catégorie",loc='center left',bbox_to_anchor=(1.02, 0.5),borderaxespad=0.,fontsize=6,title_fontsize=9, ncol=1,frameon=False)

    plt.savefig(path / 'figures_acting' / "percentage.png")
    plt.show(block=False)
    plt.pause(0.1)
    plt.close()

    # advanced heatmap with nominations in categories by decades and gender
    g = (
        df_persons_categories_top_20
        .groupby(['category', 'decade', 'gender'])
        .size()
        .unstack('gender', fill_value=0)
        .rename(columns={'female': 'F', 'male': 'M'})
    )
    # dla bezpieczeństwa – jakby którejś płci nie było wcale
    for col in ['F', 'M']:
        if col not in g.columns:
            g[col] = 0

    categories = sorted(df_persons_categories_top_20['category'].unique())
    decades = sorted(df_persons_categories_top_20['decade'].unique())

    # maxy do normalizacji kolorów
    max_f = g['F'].max() or 1
    max_m = g['M'].max() or 1

    cmap_f = plt.cm.Blues   # kobiety
    cmap_m = plt.cm.Reds    # mężczyźni

    # rysowanie wykresow

    fig, ax = plt.subplots(figsize=(min(len(decades) * 0.9,20), min(len(categories) * 0.35,24)))

    for i, cat in enumerate(categories):
        for j, dec in enumerate(decades):
            if (cat, dec) in g.index:
                f = int(g.loc[(cat, dec), 'F'])
                m = int(g.loc[(cat, dec), 'M'])
            else:
                f = m = 0
            # puste pole
            if f == 0 and m == 0:
                # delikatna kratka
                ax.add_patch(Rectangle((j, i), 1, 1,
                                       facecolor='white',
                                       edgecolor='grey',
                                       linewidth=0.5))
                continue
            # lewa polowa – kobiety
            col_f = cmap_f(f / max_f) if f > 0 else (1, 1, 1, 1)
            ax.add_patch(Rectangle((j, i), 0.5, 1,
                                   facecolor=col_f,
                                   edgecolor='darkgrey',
                                   linewidth=0.5))
            # prawa polowa – mezczyzni
            col_m = cmap_m(m / max_m) if m > 0 else (1, 1, 1, 1)
            ax.add_patch(Rectangle((j + 0.5, i), 0.5, 1,
                                   facecolor=col_m,
                                   edgecolor='darkgrey',
                                   linewidth=0.5))
            #liczba kobiet po lewej, facetow po prawej
            if f > 0:
                ax.text(j + 0.25, i + 0.5, str(f),
                        ha='center', va='center', fontsize=7, color='black')
            if m > 0:
                ax.text(j + 0.75, i + 0.5, str(m),
                        ha='center', va='center', fontsize=7, color='black')

    # osie i podpisy
    ax.set_xticks(np.arange(len(decades)) + 0.5)
    ax.set_xticklabels([f"{int(d)}s" for d in decades], rotation=45, ha='right')

    ax.set_yticks(np.arange(len(categories)) + 0.5)
    ax.set_yticklabels(categories)

    ax.set_xlim(0, len(decades))
    ax.set_ylim(0, len(categories))
    ax.invert_yaxis()

    ax.set_xlabel('Décennie')
    ax.set_ylabel('Catégorie')
    ax.set_title("Oscars : nombre de nominations par catégorie et décennie\nmoitié gauche = femmes, moitié droite = hommes")

    # termometry

    norm_f = mcolors.Normalize(vmin=0, vmax=max_f)
    norm_m = mcolors.Normalize(vmin=0, vmax=max_m)
    sm_f = plt.cm.ScalarMappable(cmap=cmap_f, norm=norm_f)
    sm_m = plt.cm.ScalarMappable(cmap=cmap_m, norm=norm_m)
    sm_f.set_array([])
    sm_m.set_array([])

    cbar_f = plt.colorbar(sm_f, ax=ax, fraction=0.03, pad=0.09)
    cbar_f.set_label("Nombre de nominations – femmes")

    cbar_m = plt.colorbar(sm_m, ax=ax, fraction=0.03, pad=0.09)
    cbar_m.set_label("Nombre de nominations – hommes")

    plt.tight_layout()
    plt.savefig(path / 'figures_gender' / 'decades_categories_gender.png')
    plt.show(block=False)
    plt.pause(0.1)
    plt.close()
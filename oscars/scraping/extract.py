import re
import sys
import pandas as pd
from bs4 import BeautifulSoup as bs, Tag
from pathlib import Path
from oscars.utils.report_gen import generate_raw_report

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INDEX_PATH = HERE / "index.html"
TRANSFORMED = ROOT / "analitics/transformed"

def _load_html():
    with INDEX_PATH.open(encoding="utf-8") as f:
        return bs(f, "html.parser")
path = Path("index.html")
pd.set_option("display.max_rows", 2000)
pd.set_option("display.max_columns", 200)
pd.set_option("display.width", 0)
pd.set_option("display.max_colwidth", None)
pd.set_option("display.expand_frame_repr", False)

def make_dict(html):
    import json
    links = [a["href"] for a in html.select("a")]
    years = [h.get_text() for h in html.select("h2")]
    pairs = dict(zip(years,links))

    def walking_through(h3_node):
        node = h3_node.next_sibling
        out = []
        while node is not None:
            if not isinstance(node, Tag):
                node = node.next_sibling
                continue

            if node is None:
                return []

            if node.name in ("h2", "h3"):
                break

            if node.name in ("p", "li"):
                out.append(node.get_text(",", strip=True))
            else:
                for el in node.find_all(["p", "li"]):
                    out.append(el.get_text(",", strip=True))
            node = node.next_sibling

        return out

    result = {}

    for k,v in pairs.items():
        print(k, v)
        page_path = Path(v) if Path(v).is_absolute() else (HERE / v)
        with open(page_path,encoding="utf-8") as page:
            html_soup = bs(page, "html.parser")
            int_year = int(k)
            result[k] = {"Year": int_year,"Link":v,"Category":{}}
            print("Petla po latach i linkch no 1")
            for x in html_soup.find_all("h2"):
                category = x.get_text(" ", strip=True)
                result[k]['Category'].setdefault(category,{"Winners":[],"Nominees":[]})
                wrapper =  x.find_parent("div",class_='category-section')
                if wrapper is None:
                    nxt = x.next_sibling
                    while nxt is not None and not isinstance(nxt, Tag):
                        nxt = nxt.next_sibling
                    if isinstance(nxt, Tag) and 'category-section' in nxt.get('class'):
                        wrapper = nxt

                if wrapper is None:
                    continue

                for h3 in wrapper.find_all("h3"):
                    title = h3.get_text(" ", strip=True).lower()
                    if re.search(r"\bwinners?\b", title):
                        result[k]["Category"][category]["Winners"].extend(
                            walking_through(h3)
                        )
                    elif re.search(r"\bnominees?\b", title):
                        result[k]["Category"][category]["Nominees"].extend(
                            walking_through(h3)
                        )

    TRANSFORMED.mkdir(parents=True, exist_ok=True)
    with (TRANSFORMED / "oscars.json").open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, sort_keys=True)

    print(result)
    return result,pairs


def flatten_awards(result: dict) -> pd.DataFrame:
    rows = []
    for year_key,payload in result.items():
        year = payload.get("Year", year_key)
        link = payload.get("Link", [])
        cats = payload.get("Category", [])
        for category,groups in cats.items():
            for items in groups.get("Winners", []):
                # print(year,"\n",link,"\n","Category: \n",category,"\nwinners: \n",items)
                rows.append({
                        "year": year,
                        "link": link,
                        "category": category,
                        "object": items,
                        "is_winner": True
                    })

            for items in groups.get("Nominees", []):
                # print(year,"\n",link,"\n","Category: \n",category,"\nnominees: \n",items)
                rows.append({
                        "year": year,
                        "link": link,
                        "category": category,
                        "object": items,
                        "is_winner": False
                    })
    return pd.DataFrame(rows)

def flattened():
    html = _load_html()
    res, _ = make_dict(html)
    df = flatten_awards(res)
    TRANSFORMED.mkdir(parents=True, exist_ok=True)

    bronze_csv = TRANSFORMED / "oscars_bronze.csv"
    report_txt = TRANSFORMED / "bronze_data_report.txt"
    diff_csv = TRANSFORMED / "bronze_with_difficulty.csv"

    df.drop_duplicates(subset=["year","link","category","object","is_winner"], inplace=True)
    df.to_csv(bronze_csv, index=False)

    rep = generate_raw_report(df, bronze_csv, report_txt, max_object_examples=20,
                              random_state=42,
                              difficulty_csv_path=diff_csv)
    print('Tu jest print: ',type(rep))

    return df

if __name__ == "__main__":
    flattened()




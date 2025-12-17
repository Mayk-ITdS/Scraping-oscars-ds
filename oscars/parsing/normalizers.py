import pandas as pd
import re

_WS = re.compile(r'\s+')

SUFFIX_TOK = r'(?:Jr|Sr|I{2,3}|IV|V)\.?'
CORP_SFX = r'(?:Inc\.?|Incorporated|Ltd|LLC|L\.L\.C\.|LLP|PLC|S\.A\.|AG|GmbH|Co\.?|Company)'
comma_not_before_suffix = r',\s*(?!(?:' + SUFFIX_TOK + r'|' + CORP_SFX + r')(?:\b|\.|,))'

SPLIT_RE = re.compile(
    r'(?:' + comma_not_before_suffix + r'|\s+(?:and|&)\s+)',
    re.I,
)
PROTECTED_AND = [
    re.compile(r'Bausch\s*&\s*Lomb', re.I),
    re.compile(r'Bell\s+and\s+Howell', re.I),
    re.compile(r'Motion\s+Picture\s+and\s+Television', re.I),
    re.compile(r'Leopold\s+Stokowski\s+and\s+his\s+associates', re.I),
    re.compile(r'the\s+National\s+Endowment\s+for\s+the\s+Arts',re.I),
    re.compile(r'Bill\s+and\s+Coo',re.I),
    re.compile(r'St.\s+Francis-Xavier\s+University,\s+Antigonish,\s+Nova\s+Scotia',re.I),
    re.compile(r'Information\s+and\s+Educational\s+Exchange', re.I),
]
def mask_protected_and(s: str) -> tuple[str, dict[str, str]]:
    repls = {}
    for i, pat in enumerate(PROTECTED_AND):
        def _rep(m):
            key = f"\x01P{i}\x02" # trick z oznaczeniem "nie ruszaj" :)
            repls[key] = m.group(0)
            return key
        s = pat.sub(_rep, s)
    return s, repls

def unmask(s: str, repls: dict[str, str]) -> str:
    for k, v in repls.items():
        s = s.replace(k, v)
    return s

def split_keep_protected(value: str) -> list[str]:

    if pd.isna(value):
        value = ""
    else:
        value = str(value).strip()
    masked, repls = mask_protected_and(value)
    masked = re.sub(
        r',\s*(?=(?:' + SUFFIX_TOK + r'|' + CORP_SFX + r')\b)',
        ' ',
        masked,
        flags=re.I,
    )
    parts = SPLIT_RE.split(masked)
    return [unmask(p.strip(), repls) for p in parts if p.strip()]

def norm_entity(s):
    if s is None or pd.isna(s):
        return pd.NA
    s = re.sub(r'\s*[-–—]\s*["“‘\'].*["”’\']\s*$', '', str(s))
    s = re.sub(r'\(\s*([^)]*?)\s*\)', r' \1 ', s)
    s = re.sub(r'(\'\s*["\s*]\s*Made\s+by\s+)\b','',s)
    s = _WS.sub(" ", s)
    s = re.sub(r'\b(Jr|Sr)\b\.?', r'\1.', s, flags=re.I)
    s = re.sub(
        r',\s*(?=(?:' + SUFFIX_TOK + r'|' + CORP_SFX + r')\b)',
        " ",
        s,
        flags=re.I,
    )
    s = re.sub(r'\s+CARNE\b.*',"",s)
    s = s.strip(" \t\r\n\u00a0,;:.()")
    return s if s else pd.NA

def norm_role(s):
    if s is None or pd.isna(s):
        return pd.NA
    s = re.sub(r'\s+', ' ', str(s).strip().lower())
    canon = {
        'original score': 'score',
        'music director': 'musical director',
        'executive producers': 'executive producer',
        'associate producers': 'associate producer',
        'producers': 'producer',
        'photographic effects': 'photographic effects',
        'sound effects': 'sound effects',
    }
    return canon.get(s, s)

def split_entity_col(df_in, col='entity'):

    if df_in is None or df_in.empty or col not in df_in.columns:
        return df_in
    g = df_in.copy()

    g[col] = g[col].astype('string').map(split_keep_protected)
    g = g.explode(col, ignore_index=True)
    g[col] = g[col].astype('string').map(norm_entity)

    return g
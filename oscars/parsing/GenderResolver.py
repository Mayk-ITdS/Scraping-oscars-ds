import re
import unicodedata as ud
from functools import lru_cache
from typing import Optional
import pandas as pd
from oscars.parsing.NamesBuffer import NamesBuffer
from oscars.parsing.normalizers import norm_role
from oscars.roles.RoleMapper import RoleMapper, _MALE_A, _FEMALE_EX, RoleDef

class GenderResolver:

    _MALE_A = _MALE_A
    _FEMALE_EX = _FEMALE_EX
    _DET = None

    @staticmethod
    def _get_detector():
        if GenderResolver._DET is None:
            try:
                from gender_guesser.detector import Detector
                GenderResolver._DET = Detector(case_sensitive=False)
            except Exception:
                GenderResolver._DET = None
        return GenderResolver._DET
    @staticmethod
    def nzstr(x):
        return "" if pd.isna(x) else str(x)
    @classmethod
    def _first_name(cls,name: str) -> str:
        s = (name or '').strip()
        if not s or s.lower() in ('nan', 'none'):
            return ''
        s = re.sub(r'\s*\([^)]*\)\s*', ' ', s)
        s = re.sub(r',\s*(Jr|Sr|I{2,3}|IV|V)\.?$', '', s, flags=re.I).strip()
        parts = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ'-]+", s)
        if not parts:
            return ''
        fn = ''.join(ch for ch in ud.normalize('NFKD', parts[0]) if not ud.combining(ch))
        return fn.lower()

    @staticmethod
    @lru_cache(maxsize=100_000)
    def _gender_from_firstname(fn: str) -> Optional[str]:
        if not fn:
            return None
        if fn in _MALE_A:
            return 'male'
        if fn in _FEMALE_EX or fn.endswith('a'):
            return 'female'
        detector = GenderResolver._get_detector()
        if detector:
            g = detector.get_gender(fn)
            g = g.casefold()
            if g in ("female", "mostly_female"):
                return 'female'
            if g in ("male", "mostly_male"):
                return 'male'
        return None
    @classmethod
    def gender_for(cls, entity: str, role: str, is_person: bool) -> Optional[str]:
        reg = NamesBuffer.registry()
        key = NamesBuffer._norm_key(entity)
        if key in reg['gender_ovr']:
            return reg['gender_ovr'][key]
        if role == 'actress': return 'female'
        if role == 'actor':   return 'male'
        if not is_person:     return None
        if key in reg['person_exp']:
            entity = reg['person_exp'][key]
        fn = GenderResolver._first_name(entity)
        return GenderResolver._gender_from_firstname(fn)

    @staticmethod
    @lru_cache(maxsize=100_000)
    def guess(entity_name: str, role_hint: Optional[str] = None) -> Optional[str]:

        raw = (entity_name or '').strip()
        if not raw:
            return None

        kind = RoleMapper.classify_entity(raw, role_hint or '')

        if kind != 'person':
            return None

        reg = NamesBuffer.registry()
        key = NamesBuffer._norm_key(raw)

        if key in reg['gender_ovr']:
            return reg['gender_ovr'][key]

        r = (role_hint or '').strip().lower()
        if r == 'actress': return 'female'
        if r == 'actor':   return 'male'

        if key in reg['person_exp']:
            raw = reg['person_exp'][key]

        fn = GenderResolver._first_name(raw)
        return GenderResolver._gender_from_firstname(fn)

    def harmonize_roles(df: pd.DataFrame, role_col="role", category_col="category") -> pd.DataFrame:
        rows = []
        for _, row in df.iterrows():
            raw_role = row.get(role_col, None)
            raw_cat  = row.get(category_col, "")

            if raw_role is not None and not pd.isna(raw_role):
                role_txt = norm_role(raw_role)
            else:
                role_txt = ""
            cat_txt  = str(raw_cat).strip().lower()

            # fallback typu: nie ma to wez z kategorii
            if not role_txt and cat_txt:
                role_txt = norm_role(cat_txt)

            # podstawowe role
            defs = RoleMapper.map_role_defs(role_txt, cat_txt)

            fixed_defs = []
            for d in defs:
                sub = d.subtype
                # role function i sub
                if d.role in ("actor", "actress"):
                    text_all = f"{role_txt} {cat_txt}"
                    if "support" in text_all:
                        sub = "supporting"
                    elif "lead" in text_all:
                        sub = "leading"
                fixed_defs.append(RoleDef(d.role, d.function, sub, d.include))

            for d in fixed_defs:
                ent = GenderResolver.nzstr(row.get("entity")).strip()
                kind = RoleMapper.classify_entity(ent, d.role)
                gender = GenderResolver.gender_for(ent, d.function, kind == "person")

                out = row.to_dict()
                out.update(
                    {
                        "role": d.role,
                        "role_function": d.function,
                        "role_subtype": d.subtype,
                        "include_role": d.include,
                        "entity_type": kind,
                        "is_person": kind == "person",
                        "gender": gender,
                    }
                )
                rows.append(out)

        return pd.DataFrame(rows)


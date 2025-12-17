from dataclasses import dataclass
from typing import Optional, List, Dict
import re
import pandas as pd
from oscars.parsing.NamesBuffer import NamesBuffer

_MALE_A = {'kuba','joshua','andrea','arnold','allah','sasha','misha','nikita','luca','nikola','ilya','ilia','pasha','tolya','noa'}
_FEMALE_EX: set[str] = set()

@dataclass(frozen=True)
class RoleDef:
    role: str
    function: str
    subtype: Optional[str] = None
    include: bool = True

class RoleMapper:
    CATEGORY_ALIASES = {
        # craft rozbite na bw i color
        "cinematography (black-and-white)": "cinematography",
        "cinematography (color)": "cinematography",
        "art direction (black-and-white)": "art direction",
        "art direction (color)": "art direction",
        "costume design (black-and-white)": "costume design",
        "costume design (color)": "costume design",

        # documentary
        "documentary (feature)": "documentary feature film",
        "documentary (short subject)": "documentary short film",
        "documentary": "documentary",
        "directing (comedy picture)": "directing",
        "directing (dramatic picture)": "directing",
        # shorty
        "short film (animated)": "short film",
        "short film (live action)": "short film",
        "short subject (cartoon)": "short subject",
        "short subject (color)": "short subject",
        "short subject (comedy)": "short subject",
        "short subject (live action)": "short subject",
        "short subject (novelty)": "short subject",
        "short subject (one-reel)": "short subject",
        "short subject (two-reel)": "short subject",

        # language
        "honorary foreign language film award": "foreign language film",
        "special foreign language film award": "foreign language film",

        # special / honorary
        "award of commendation": "special",
        "special achievement award (sound editing)": "special achievement award",
        "special achievement award (sound effects editing)": "special achievement award",
        "special achievement award (sound effects)": "special achievement award",
        "special achievement award (visual effects)": "special achievement award",
    }
    VOCAB: Dict[str, List[RoleDef]] = {
        'actor': [RoleDef('acting','actor','leading')],
        'actor in a leading role': [RoleDef('acting','actor', 'leading')],
        'actor in a supporting role': [RoleDef('acting','actor','supporting')],
        'actress': [RoleDef('acting','actress','leading')],
        'actress in a leading role': [RoleDef('acting','actress','leading')],
        'actress in a supporting role': [RoleDef('acting','actress','supporting')],
        'producer': [RoleDef('producing','producer')],
        'executive producer': [RoleDef('producing','producer','executive')],
        'associate producer': [RoleDef('producing','producer','associate')],
        'best motion picture': [RoleDef('producing', 'picture_producer','best_motion')],
        'outstanding motion picture': [RoleDef('producing', 'picture_producer','outstanding')],
        'outstanding picture': [RoleDef('producing', 'picture_producer','outstanding')],
        'outstanding production': [RoleDef('producing','picture_producer','outstanding',include=True)],
        'unique and artistic picture': [RoleDef('producing', 'picture_producer','unique_and_artistic')],
        'directing': [RoleDef('directing','film_director','unspecified')],
        'screenplay': [RoleDef('writing','screenplay_writer', 'original')],
        'screenplay and dialogue': [RoleDef('writing','screenplay_writer', 'original')],
        'story': [RoleDef('writing', 'story_writer','original',include=True)],
        'written': [RoleDef('writing', 'screenplay_writer','original',include=True)],
        'writer': [RoleDef('writing', 'screenplay_writer','original')],
        'adapted': [RoleDef('writing','screenplay_writer', 'adapted')],
        'animated feature film': [RoleDef('producing','film_producer', 'animated_feature', include=True)],
        'international feature film': [RoleDef('producing','film_producer', 'international_feature', include=True)],
        'foreign language film': [RoleDef('producing','film_producer','foreign_language_movie', include=True)],
        'documentary': [RoleDef('producing','film_producer', 'documentary', include=True)],
        'documentary feature film': [RoleDef('producing','film_producer', 'documentary_feature', include=True)],
        'documentary short film': [RoleDef('producing','film_producer', 'documentary_short', include=True)],
        'short film': [RoleDef('producing','film_producer','short', include=True)],
        'short subject': [RoleDef('producing','film_producer','short', include=True)],
        'cinematography': [RoleDef('visual','cinematographer', 'photography')],
        "ballet photography": [RoleDef('visual','cinematographer','photography',include=True)],
        'film editing': [RoleDef('visual', 'film_editor','unspecified')],
        'production design': [RoleDef('visual', 'designer','production_design')],
        'art direction': [RoleDef('visual', 'art_director')],
        'set decoration': [RoleDef('visual','set_decorator')],
        'interior decoration': [RoleDef('visual','decorator','interior_decoration')],
        'costume design': [RoleDef('visual','designer','costume_designer')],
        'makeup': [RoleDef('visual','makeup_artist','artistic_craft')],
        'makeup and hairstyling': [RoleDef('visual','makeup_&_hairstyle','artistic_craft'), RoleDef('visual','hairstylist', 'artistic_craft')],
        'score': [RoleDef('music', 'composer', 'score_writing')],
        'scoring': [RoleDef('music', 'composer', 'score_writing')],
        'adaptation score': [RoleDef('music', 'composer', 'score_adaptation')],
        'song score': [RoleDef('music', 'composer', 'song_score')],
        'lyrics': [RoleDef('writing', 'lyricist', 'song_lyrics')],
        'lyric': [RoleDef('writing', 'lyricist', 'song_lyrics',include=True)],
        'music and lyric': [RoleDef('music', 'composer', 'music_composer',include=True), RoleDef('writing', 'lyricist', 'song_lyrics',include=True)],
        'music and lyrics': [RoleDef('music', 'composer', 'music_composer',include=True), RoleDef('writing', 'lyricist', 'song_lyrics',include=True)],
        'music': [RoleDef('music', 'composer','unspecified',include=True)],
        'sound': [RoleDef('audio', 'sound_designer','unknown')],
        'sound mixing': [RoleDef('audio','sound_designer', 'sound_mixing')],
        'sound editing': [RoleDef('audio','sound_designer', 'sound_editing')],
        'sound effects': [RoleDef('audio','sound_designer', 'sound_effects')],
        'sound effects editing': [RoleDef('audio', 'sound_editor', 'sound_effects')],
        'sound director': [RoleDef('audio', 'sound_director', 'unspecified')],
        'recording_studio': [RoleDef('audio', 'sound_designer','recording_studio', include=False)],
        'studio': [RoleDef('audio', 'sound_designer', 'recording_studio', include=False)],
        'radio': [RoleDef('audio', 'sound_designer', 'radio', include=False)],
        'country': [RoleDef('country', 'geopolitical', include=False)],
        'movie': [RoleDef('visual','film_work', 'work', include=False)],
        'film': [RoleDef('visual','film_work', 'work', include=False)],
        'visual effects': [RoleDef('visual', 'special_effects','visual_effects')],
        'visual':[RoleDef('visual', 'special_effects','visual_effects',include=True)],
        'special effects': [RoleDef('visual','special_effects', 'vfx')],
        'audible effects': [RoleDef('audio','sound_designer','audio_effects',include=True)],
        'audible': [RoleDef('audio','sound_designer','audio_effects',include=True)],
        'special audible effects': [RoleDef('audio','sound_designer','audible_effects',include=True)],
        'special visual effects': [RoleDef('visual','special_effects','visual_effects',include=True)],
        'photographic effects': [RoleDef('visual','special_effects','photographic_effects',include=True)],
        'engineering effects': [RoleDef('visual', 'special_effects','engineering_effects',include=True)],
        'assistant director': [RoleDef('directing', 'film_director','assistant_director', include=True)],
        'musical director': [RoleDef('directing', 'film_director','musical_director', include=True)],
        'head of department': [RoleDef('directing','head_of_department','department_director', include=True)],
        'performer': [RoleDef('visual','performer', 'artist', include=True)],
        'dance direction': [RoleDef('visual','choreographer', 'artist', include=True)],
        'musical settings': [RoleDef('music', 'music_arranger','scores', include=True)],
        'honorary': [RoleDef('honorary', 'honorary_recipient','unknown', include=True)],
        'honorary award': [RoleDef('honorary', 'honorary_recipient','unknown', include=True)],
        'special award': [RoleDef('special', 'special_recipient','unknown', include=True)],
        'AWARD OF COMMENDATION':[RoleDef('special','commendation_recipient','unknown',include=True)],
        'award of commendation': [RoleDef('special', 'commendation_recipient', 'unknown', include=True)],
        'special achievement award': [RoleDef('special', 'achievement_recipient', include=True)],
        'irving g. thalberg memorial award': [RoleDef('memorial', 'memorial_award_recipient','irving_thalberg_award', include=True)],
        'jean hersholt humanitarian award': [RoleDef('humanitarian', 'humanitarian_award_recipient','jean_hersholt_award', include=True)],
        'gordon e. sawyer award': [RoleDef('honorary', 'gordon_recipient', include=True)],
        'pioneer': [RoleDef('', 'honorary', include=True)],
        '<unset>': [RoleDef('', 'other', include=True)],
        '': [RoleDef('', 'other', include=False)],
        None: [RoleDef('', 'other', include=False)],
    }
    ORG_FORCE = {'company','government','recording_studio','studio','radio'}

    @staticmethod
    def _norm_text(s) -> str:
        if s is None or pd.isna(s):
            return ''
        return re.sub(r'\s+', ' ', str(s).strip().lower())

    @classmethod
    def map_role_defs(cls, role_txt: str, category: str) -> List[RoleDef]:
        key_raw  = cls._norm_text(role_txt)
        cat_raw = cls._norm_text(category)
        cat = cls.CATEGORY_ALIASES.get(cat_raw, cat_raw)

        if "honorary" in cat:
            key = 'honorary award'
        else:
            key = key_raw
            if key not in cls.VOCAB:
                key_aliases = cls.CATEGORY_ALIASES.get(key_raw,key_raw)
                key = key_aliases
            elif not key or key == cat_raw:
                key=cat
        defs = cls.VOCAB.get(key, [RoleDef('special', 'special_recipient', include=False)])

        out: List[RoleDef] = []
        for d in defs:
            sub = d.subtype
            if d.role in ('actor','actress'):
                if (sub is None or sub == 'leading') and 'support' in cat:
                    sub = 'supporting'
                elif sub is None and 'leading' in cat:
                    sub = 'leading'
            if d.role == 'screenwriter':
                if (sub is None or sub == 'original') and 'adapt' in cat:
                    sub = 'adapted'
                elif sub is None and ('original' in cat or 'story' in cat):
                    sub = 'original'
            out.append(RoleDef(d.role, d.function, sub, d.include))
        return out

    @classmethod
    def classify_entity(cls, entity: str, role: str) -> str:
        raw = (entity or '').strip()
        if not raw:
            return 'unknown'
        if NamesBuffer.is_country(raw):
            return 'country'
        if role in cls.ORG_FORCE:
            return 'company'
        reg = NamesBuffer.registry()
        key = NamesBuffer._norm_key(raw)
        if key in reg['groups']:
            return 'group'
        if key in reg['org_overrides'] or reg['org_re'].search(raw):
            return 'company'
        if key in reg['movies']:
            return 'film'
        return 'person'

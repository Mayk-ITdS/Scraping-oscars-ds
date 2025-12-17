import re

class RegexPatterns:
    class Base:
        _WS = re.compile(r'\s+')
        SUFFIX_TOK = r'(?:Jr|Sr|I{2,3}|IV|V)\.?'
        CORP_SFX = r'(?:Inc\.?|Incorporated|Ltd|LLC|L\.L\.C\.|LLP|PLC|S\.A\.|AG|GmbH|Co\.?|Company)'

        comma_not_before_suffix = r',\s*(?!(?:' + SUFFIX_TOK + r'|' + CORP_SFX + r')(\b|\.))'
        SPLIT_PAT = r'(?:' + comma_not_before_suffix + r'|\s+(?:and|&)\s+)'

        role_token_pat = r'(?i)^(?:sound\s+director|music(?:al)?\s+director|art\s+director|director\s+of\s+photography|head\s+of\s+department|score)$'
        forbidden_entity_pat = r'(?i)\b(?:by|head\s+of\s+department|music(?:al)?\s+director|director\s+of\s+photography|art\s+director|score(?:\s+by)?|no\s+composer\s+credit)\b'
        NAME_CORE = r"[A-Za-zÀ-ÖØ-öø-ÿ .'\-]+"
        allowed_name = rf"^{NAME_CORE}(?:,\s*(?:{SUFFIX_TOK}|{CORP_SFX}))?(?:\s*\([^)]+\))?$"

    class Entity:
        pat_pairs = re.compile(r'''(?ix)
                (?P<role>[A-Z][\w\s.&/\-]*?)\s*:\s*
                (?P<people>.*?)
                (?=(?:\s*;\s*)?(?:[A-Z][\w\s.&/\-]*\s*:)|$)
            ''')
        pat_paren_entity = re.compile(r'''(?ix)
                   ^\s*(?P<entity>[^,(]+?\s*\([^)]+\))\s*(?:[-–—].*)?$
               ''')
        pat_head = re.compile(r'''(?ix)
                   ^\s*(?P<dept>[^,;:()]*\b(?:studio(?:s)?\s+\w+\s+department|\w+\s+department|studio(?:s)?|radio)\b[^,;:()]*)\s*,\s*
                   (?P<head>[^,;:()]+?)\s*,\s*head\s+of\s+(?:the\s+)?department\b
               ''')
        pat_name_producer = re.compile(r"""(?xi)
               (?:^|;\s*)                                  
               (?P<entity>[^;]+?)                         
               \s*,\s*
               (?P<role>(?:executive|associate)?\s*producers?)  
               (?=\s*(?:;|$))                              
           """)
    class Screenplay:
        pattern_written = re.compile(r'''(?ix)
               (?:
                   (?P<role>
                       (?:screenplay|story|written|script|adapted|teleplay
                        |score|song\s+score|adaptation\s+score)
                   )
                   \s*[-–—]\s*
                   (?P<entity>
                       [A-Z][^;,:()"]*?
                       (?:(?!\b(?:screenplay|story|written|script|adapted|teleplay
                                 |music(?:\s+and\s+lyrics)?|lyrics?|score|song\s+score|adaptation\s+score)\b).)*?
                   )
                   (?=\s*(?:;|$|,(?=\s*(?:screenplay|story|written|script|adapted|teleplay
                                         |music(?:\s+and\s+lyrics)?|lyrics?|score|song\s+score|adaptation\s+score)\b)))
               )
               |
               (?:
                   (?P<role2>
                       (?:screenplay|ballet\s+photography|story|written|script|adapted|teleplay
                        |score|song\s+score|adaptation\s+score)
                   )
                   (?:\s+for\s+the\s+screen)?\s+\bby\b\s+
                   (?P<entity2>
                       [A-Z][^;,:()"]*?
                       (?:(?!\b(?:screenplay|story|written|script|adapted|teleplay
                                 |score|song\s+score|adaptation\s+score)\b).)*?
                   )
                   (?=\s*(?:;|$|,(?=\s*(?:screenplay|story|written|script|adapted|teleplay
                                         |score|song\s+score|adaptation\s+score)\b)))
               )
           ''')
    class Notes:
        preamble_pat_note = re.compile(r"""(?xi)
        ^\s* [‘’'"“”„«»]* \s*
        (?P<prefix>Made|Presented|Sponsored|Produced)\s+by\s+
        (?P<entity>[^,;–—-].*?)
        (?:\s*[,;:–—-]\s* |\s+)(?P<note>(?:a\s+|for|whose|who|with|as|in\s+recognition|in\s+appreciation|acknowledg\w*|voted\s+by|presented\s+to)
                    \b[\s\S]*?)
        \s*$
        """)
        pattern_note = re.compile(r"""(?xi)
                ^\s*
                (?:To\s+)?
                (?!\bthe\s+National\s+Endowment\s+for\b)
                (?!(?:Written|Writing|Screenplay|Adapted|Story|Script|Producers?|Producer|Actor|Actress|\'Made\s+by)\b)
                (?P<entity>.*?)
                \s*
                (?:,\s*(?P<roles>(?:[A-Za-z][A-Za-z\s]+?)(?:\s*,\s*[A-Za-z][A-Za-z\s]+?)*))?
                (?=
                    \s*(?:                     
                        [-–—]\s+[a-z]           
                      | ,\s*(?:a\s+|for|whose|who|with|as|in\s+recognition|in\s+appreciation|acknowledg\w*|voted\s+by|presented\s+to)\b
                                               
                      | \s+(?:a\s+|for|whose|who|with|as|in\s+recognition|in\s+appreciation|acknowledg\w*|voted\s+by|presented\s+to)\b
                                                
                    )
                )
                \s*
                (?:[-–—]\s*(?=[a-z]))?           
                (?:,\s+)?                        
                (?P<note>
                    (?:a\s+|the|for|whose|who|with|as|in\s+recognition|in\s+appreciation|acknowledg\w*|voted\s+by|presented\s+to)
                    \b[\s\S]*?                  
                )
                [.!?]?\s*$
            """)
        pattern_note_only = re.compile(r"""(?ix)
                    ^\s*
                    (?P<note>
                        (?:for\b|in\s+(?:recognition|appreciation)\b|with\s+thanks\b)[\s\S]*?
                    )
                    \s*$
                """)
    class Studio:
        pat_leading_entity_before_semicolon = re.compile(r"""(?xi)
            ^\s*
            (?![^;]*\b(                                     
                Music\s+and\s+Lyrics?|
                Music|Lyrics?|
                Song\s+Score|Adaptation\s+Score|
                Visual\s+Effects|Special\s+Visual\s+Effects|
                Special\s+Audible\s+Effects|Audible\s+Effects|
                Photographic\s+Effects|Sound\s+Effects|
                Screenplay\s+and\s+Dialogue|Score|
                Ballet\s+Photography
            )\b)
            (?P<entity>   
               [^:()]+?)                     
            
            \s*;\s*
            (?=[^:]\s*\b(                                      
                Music\s+and\s+Lyrics?|
                Music|Lyrics?|
                Song\s+Score|Adaptation\s+Score|
                Visual\s+Effects|Special\s+Visual\s+Effects|
                Special\s+Audible\s+Effects|Audible\s+Effects|
                Photographic\s+Effects|Sound\s+Effects|
                Screenplay\s+and\s+Dialogue|Score|
                Ballet\s+Photography
            )\s+by\b)
        """)
        pat_by_paren = re.compile(r"""(?ix)
                (?:(?<=^)|(?<=;)|(?<=\())\s*                
                (?P<role>
                    Music\s+and\s+Lyrics?
                  | Music
                  | Lyrics?
                  | Song\s+Score
                  | Adaptation\s+Score
                  | Visual\s+Effects
                  | Special\s+Visual\s+Effects
                  | Special\s+Audible\s+Effects
                  | Audible\s+Effects
                  | Photographic\s+Effects
                  | Sound\s+Effects
                  | Screenplay\s+and\s+Dialogue
                  | Score
                )
                (?:\s*:\s*|\s+\bby\b)\s*                     
                (?P<entity>[^;()]+?)                         
                (?=\s*(?:;|\)|$|\s+[-–—]))     
            """)
        pat_studio = re.compile(r'''(?ix)
                ^\s*(?P<studio_name>[^,;:()]*\b(?:studios?|department|radio)\b(?:(?!\s+for\b)[^,;:()])*) 
                
                (?:,\s*(?P<sound_director>[^;:()](?:Sound Director)+))?
                \s*$
            ''')
        pattern_musicdir_segment = re.compile(r"""(?ix)
                (?:^|[;(])\s*                                            
                (?:
                    (?P<head>[^,;()]*\b(?:studio(?:s)?|department|productions?|radio)\b[^,;()]*)\s*,\s*
                )?                                                      
                (?P<people>[^,;()]+?)\s*,\s*                             
                (?P<role>music(?:al)?\s+director)\b                      
                (?=\s*(?:[;)]|$|\())                                     
            """)
        pattern_person_role_producer = re.compile(r"""(?xi)
                ^\s*
                (?P<entity>[A-Z][A-Za-zÀ-ÖØ-öø-ÿ.'`\-\s]+?)      
                \s*,\s*
                (?P<role>(?:executive|associate)?\s*producer)s?  
                \s*\.?\s*
                \(\s*(?P<note>[^)]+)\s*\)                        
                \s*$
            """)
        pattern_foreign_first_release = re.compile(r"""(?xi)
                ^\s*
                (?P<title>[^-;()]+?)                
                \s*[-–—]\s*
                Best\s+Foreign\s+Language\s+Film\s+
                (?P<note>first\s+released\s+in\s+the\s+United\s+States\s+during\s+\d{4}\.?)
                \s*$
            """)
        pat_sd_segment_new = re.compile(r"""(?ix)
                        (?:^|;\s*(?:and\s+)?)\s*   
                        (?:\(\s*)?                                          
                        (?P<affiliation>[^,;()]+(?:,[^,;()]+)*)
                        \s*,\s*
                        (?P<person>[^;()]+?)                                       
                        \s*,\s*
                        (?P<role>Sound\s+Directors?)\b
                        (?:\s*\))?
                        (?=\s*(?:;|$))                                          
                    """)

        pat_sd_segment = re.compile(r"""(?ix)
                (?:\(\s*)?                                                 
                (?:
                    (?P<head>[^,;()]*\b(?:studios?|production|department|radio)\b(?:(?!\s+for\b)[^,;()])*)\s*,\s*  
                )?
                (?P<people>[^;()]+?)                                       
                (?=,\s*Sound\s+Director(?:s)?\b)                           
                \s*,\s*Sound\s+Director(?:s)?\b                            
                (?:\s*\))?                                                 
            """)
        pat_sound_parentheses = re.compile(r'''(?xi)^(?P<person>[A-Za-zÀ-ÖØ-öø-ÿ][^():;,"]+?)
                                               \s+\(\s*(?P<affiliation>(?:\s*fox|united\s+artists|radio|universal|warner\s+bros\.?|Metro-Goldwyn-Mayer|Paramount|Fox|Universal)\.*)\)$''')
    @classmethod
    def all(cls):
        return  {
        'entity_paren': cls.Entity.pat_paren_entity,
        'role_pairs': cls.Entity.pat_pairs,
        'producers':cls.Studio.pattern_person_role_producer,
        'role_by_paren': cls.Studio.pat_by_paren,
        "preamble note":cls.Notes.preamble_pat_note,
        'note': cls.Notes.pattern_note,
        'foreign movie':cls.Studio.pattern_foreign_first_release,
        'written by':cls.Screenplay.pattern_written,
        'studio_head': cls.Entity.pat_head,
        'studio_name_producer': cls.Entity.pat_name_producer,
        'studio': cls.Studio.pat_studio,
        'musical director':cls.Studio.pattern_musicdir_segment,
        'sound director':cls.Studio.pat_sd_segment,
        'new_sound_frame':cls.Studio.pat_sd_segment_new,
        'new_sound_frame_parenthesis':cls.Studio.pat_sound_parentheses,
    }


text = "James Price and Shona Heath; Set Decoration: Zsuzsa Mihalek"
print(re.split(RegexPatterns.Base.SPLIT_PAT, text))
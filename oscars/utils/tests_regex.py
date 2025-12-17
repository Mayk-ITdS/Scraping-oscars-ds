import csv
import re
from textwrap import dedent
import pandas as pd

from oscars.parsing.RegexPatterns import RegexPatterns
#
# affil_only_pat = re.compile(r"""(?ix)
# ^\s*["']?\(?\s*
# (?P<affiliation>
#     (?:[^"':()]+?)
#     (?:
#         Studios?
#       | Sound\s+Department
#       | Film\s+Studios?
#       | Productions?
#       | Production(?:\s+Company)?
#       | Pictures
#       | Radio
#       | Department
#       | Services?
#       | Office
#       | Unit
#     )
#     [^"':()]*
# )
# \s*\)?["']?\s*$
# """)
#
# raw_text = dedent("""
# Shepperton Studio Sound Department
# Warner Bros.-Seven Arts Studio Sound Department
# Warner Bros.-Seven Arts Studio Sound Department
# Columbia Studio Sound Department
# 20th Century-Fox Studio Sound Department
# Samuel Goldwyn Studio Sound Department
# Warner Bros.-Seven Arts Studio Sound Department
# Metro-Goldwyn-Mayer Studio Sound Department
# 20th Century-Fox Studio Sound Department
# Universal City Studio Sound Department
# Mafilm Studio
# "Metro-Goldwyn-Mayer Studio Sound Department, Franklin E. Milton, Sound Director"
# "Universal City Studio Sound Department, Waldon O. Watson, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Gordon E. Sawyer, Sound Director"
# "20th Century-Fox Studio Sound Department, James P. Corcoran, Sound Director"
# "Warner Bros. Studio Sound Department, George R. Groves, Sound Director"
# "20th Century-Fox Studio Sound Department, James P. Corcoran, Sound Director; and Todd-AO Sound Department, Fred Hynes, Sound Director"
# "20th Century-Fox Studio Sound Department, James P. Corcoran, Sound Director; and Todd-AO Sound Department, Fred Hynes, Sound Director"
# "20th Century-Fox Studio Sound Department, James P. Corcoran, Sound Director"
# "Metro-Goldwyn-Mayer British Studio Sound Department, A. W. Watkins, Sound Director; and Metro-Goldwyn-Mayer Studio Sound Department, Franklin E. Milton, Sound Director"
# "Metro-Goldwyn-Mayer British Studio Sound Department, A. W. Watkins, Sound Director; and Metro-Goldwyn-Mayer Studio Sound Department, Franklin E. Milton, Sound Director"
# "Warner Bros. Studio Sound Department, George R. Groves, Sound Director"
# "Universal City Studio Sound Department, Waldon O. Watson, Sound Director"
# "Warner Bros. Studio Sound Department, George R. Groves, Sound Director"
# "Shepperton Studio Sound Department, John Cox, Sound Director"
# "Universal City Studio Sound Department, Waldon O. Watson, Sound Director"
# "Walt Disney Studio Sound Department, Robert O. Cook, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Franklin E. Milton, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Franklin E. Milton, Sound Director"
# "Columbia Studio Sound Department, Charles Rice, Sound Director"
# "Universal City Studio Sound Department, Waldon O. Watson, Sound Director"
# "20th Century-Fox Studio Sound Department, James P. Corcoran, Sound Director; and Todd-AO Sound Department, Fred Hynes, Sound Director"
# "20th Century-Fox Studio Sound Department, James P. Corcoran, Sound Director; and Todd-AO Sound Department, Fred Hynes, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Gordon E. Sawyer, Sound Director"
# "Shepperton Studio Sound Department, John Cox, Sound Director"
# "Walt Disney Studio Sound Department, Robert O. Cook, Sound Director"
# "Warner Bros. Studio Sound Department, George R. Groves, Sound Director"
# "Universal City Studio Sound Department, Waldon O. Watson, Sound Director"
# "Glen Glenn Sound Department, Joseph Kelly, Sound Director"
# Templar Film Studios
# "Todd-AO Sound Department, Fred Hynes, Sound Director; and Samuel Goldwyn Studio Sound Department, Gordon E. Sawyer, Sound Director"
# "Todd-AO Sound Department, Fred Hynes, Sound Director; and Samuel Goldwyn Studio Sound Department, Gordon E. Sawyer, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Gordon E. Sawyer, Sound Director"
# "Revue Studio Sound Department, Waldon O. Watson, Sound Director"
# "Shepperton Studio Sound Department, John Cox, Sound Director"
# "Walt Disney Studio Sound Department, Robert O. Cook, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Gordon E. Sawyer, Sound Director; and Todd-AO Sound Department, Fred Hynes, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Gordon E. Sawyer, Sound Director; and Todd-AO Sound Department, Fred Hynes, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Gordon E. Sawyer, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Franklin E. Milton, Sound Director"
# "Columbia Studio Sound Department, Charles Rice, Sound Director"
# "Warner Bros. Studio Sound Department, George R. Groves, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Franklin E. Milton, Sound Director"
# "20th Century-Fox Studio Sound Department, Carl Faulkner, Sound Director"
# "Metro-Goldwyn-Mayer London Studio Sound Department, A. W. Watkins, Sound Director"
# "Warner Bros. Studio Sound Department, George R. Groves, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Gordon E. Sawyer, Sound Director; and Todd-AO Sound Department, Fred Hynes, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Gordon E. Sawyer, Sound Director; and Todd-AO Sound Department, Fred Hynes, Sound Director"
# "Todd-AO Sound Department, Fred Hynes, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Gordon E. Sawyer, Sound Director"
# "Universal-International Studio Sound Department, Leslie I. Carey, Sound Director"
# "Paramount Studio Sound Department, George Dutton, Sound Director"
# "20th Century-Fox Studio Sound Department, Carl Faulkner, Sound Director"
# "Warner Bros. Studio Sound Department, George Groves, Sound Director"
# "Paramount Studio Sound Department, George Dutton, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Dr. Wesley C. Miller, Sound Director"
# "Columbia Studio Sound Department, John P. Livadary, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Gordon E. Sawyer, Sound Director"
# "20th Century-Fox Studio Sound Department, Carl Faulkner, Sound Director"
# "King Bros. Productions, Inc., Sound Department, John Myers, Sound Director"
# "King Bros. Productions, Inc., Sound Department, John Myers, Sound Director"
# "King Bros. Productions, Inc., Sound Department, John Myers, Sound Director"
# "Columbia Studio Sound Department, John Livadary, Sound Director"
# "Westrex Sound Services, Inc., Gordon R. Glennan, Sound Director; and Samuel Goldwyn Studio Sound Department, Gordon Sawyer, Sound Director"
# "Westrex Sound Services, Inc., Gordon R. Glennan, Sound Director; and Samuel Goldwyn Studio Sound Department, Gordon Sawyer, Sound Director"
# "Westrex Sound Services, Inc., Gordon R. Glennan, Sound Director; and Samuel Goldwyn Studio Sound Department, Gordon Sawyer, Sound Director"
# "Paramount Studio Sound Department, Loren L. Ryder, Sound Director"
# "Todd-AO Sound Department, Fred Hynes, Sound Director"
# "20th Century-Fox Studio Sound Department, Carl W. Faulkner, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Wesley C. Miller, Sound Director"
# "Warner Bros. Studio Sound Department, William A. Mueller, Sound Director"
# "Radio Corporation of America Sound Department, Watson Jones, Sound Director"
# Paramount Studio
# 20th Century-Fox Studio
# "Universal-International Studio Sound Department, Leslie I. Carey, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Wesley C. Miller, Sound Director"
# "Columbia Studio Sound Department, John P. Livadary, Sound Director"
# "Paramount Studio Sound Department, Loren L. Ryder, Sound Director"
# "RKO Radio Studio Sound Department, John O. Aalberg, Sound Director"
# Walt Disney Studios
# 20th Century-Fox Studio
# Warner Bros. Studio
# "Columbia Studio Sound Department, John P. Livadary, Sound Director"
# "Warner Bros. Studio Sound Department, William A. Mueller, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, A. W. Watkins, Sound Director"
# "Universal-International Studio Sound Department, Leslie I. Carey, Sound Director"
# "Paramount Studio Sound Department, Loren L. Ryder, Sound Director"
# Paramount Studio
# London Film Sound Department
# "Samuel Goldwyn Studio Sound Department, Gordon Sawyer, Sound Director"
# Pinewood Studios Sound Department
# "Republic Studio Sound Department, Daniel J. Bloomberg, Sound Director"
# "20th Century-Fox Studio Sound Department, Thomas T. Moulton, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Douglas Shearer, Sound Director"
# "Universal-International Studio Sound Department, Leslie I. Carey, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Gordon Sawyer, Sound Director"
# "Warner Bros. Studio Sound Department, Col. Nathan Levinson, Sound Director"
# "RKO Radio Studio Sound Department, John O. Aalberg, Sound Director"
# "20th Century-Fox Studio Sound Department, Thomas T. Moulton, Sound Director"
# "Walt Disney Studio Sound Department, C. O. Slyfield, Sound Director"
# "Universal-International Studio Sound Department, Leslie I. Carey, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Gordon Sawyer, Sound Director"
# "Pinewood Studio Sound Department, Cyril Crowhurst, Sound Director"
# "20th Century-Fox Studio Sound Department, Thomas T. Moulton, Sound Director"
# "Universal-International Studio Sound Department, Leslie I. Carey, Sound Director"
# "Republic Studio Sound Department, Daniel J. Bloomberg, Sound Director"
# "20th Century-Fox Studio Sound Department, Thomas T. Moulton, Sound Director"
# "Warner Bros. Studio Sound Department, Col. Nathan O. Levinson, Sound Director"
# "Republic Studio Sound Department, Daniel J. Bloomberg, Sound Director"
# United States Department of State Office of Information and Educational Exchange
# United States Department of State Office of Information and Educational Exchange
# RKO Radio
# "Samuel Goldwyn Studio Sound Department, Gordon Sawyer, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Douglas Shearer, Sound Director"
# "Sound Service, Inc., Jack R. Whitney, Sound Director"
# "Sound Service, Inc., Jack R. Whitney, Sound Director"
# United States Department of War
# "Columbia Studio Sound Department, John Livadary, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Gordon Sawyer, Sound Director"
# "RKO Radio Studio Sound Department, John Aalberg, Sound Director"
# "RKO Radio Studio Sound Department, Stephen Dunn, Sound Director"
# "Republic Studio Sound Department, Daniel J. Bloomberg, Sound Director"
# "Universal Studio Sound Department, Bernard B. Brown, Sound Director"
# "20th Century-Fox Studio Sound Department, Thomas T. Moulton, Sound Director"
# "Warner Bros. Studio Sound Department, Nathan Levinson, Sound Director"
# "Columbia Studio Sound Department, John P. Livadary, Sound Director"
# "General Service, Jack Whitney, Sound Director"
# "General Service, Jack Whitney, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Douglas Shearer, Sound Director"
# "Walt Disney Studio Sound Department, C. O. Slyfield, Sound Director"
# "RCA Sound, W. V. Wolfe, Sound Director"
# "RCA Sound, W. V. Wolfe, Sound Director"
# "Paramount Studio Sound Department, Loren L. Ryder, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Gordon Sawyer, Sound Director"
# Republic Studio
# RKO Radio
# "20th Century-Fox Studio Sound Department, E. H. Hansen, Sound Director"
# "Republic Studio Sound Department, Daniel J. Bloomberg, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Thomas T. Moulton, Sound Director"
# "Columbia Studio Sound Department, John Livadary, Sound Director"
# "Paramount Studio Sound Department, Loren L. Ryder, Sound Director"
# "Universal Studio Sound Department, Bernard B. Brown, Sound Director"
# "Warner Bros. Studio Sound Department, Nathan Levinson, Sound Director"
# "Sound Service, Inc., Jack Whitney, Sound Director"
# "Sound Service, Inc., Jack Whitney, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Douglas Shearer, Sound Director"
# "RKO Radio Studio Sound Department, Stephen Dunn, Sound Director"
# "RCA Sound, W. M. Dalgleish, Sound Director"
# "RCA Sound, W. M. Dalgleish, Sound Director"
# United States Department of War Special Service Division
# Australian Department of Information Film Unit
# RKO Radio
# United States Department of War
# "RKO Radio Studio Sound Department, Stephen Dunn, Sound Director"
# "Sound Service, Inc., Jack Whitney, Sound Director"
# "Sound Service, Inc., Jack Whitney, Sound Director"
# "Republic Studio Sound Department, Daniel J. Bloomberg, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Douglas Shearer, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Thomas T. Moulton, Sound Director"
# "Universal Studio Sound Department, Bernard B. Brown, Sound Director"
# "Paramount Studio Sound Department, Loren L. Ryder, Sound Director"
# "Columbia Studio Sound Department, John Livadary, Sound Director"
# "Walt Disney Studio Sound Department, C. O. Slyfield, Sound Director"
# "RCA Sound, J. L. Fields, Sound Director"
# "RCA Sound, J. L. Fields, Sound Director"
# "20th Century-Fox Studio Sound Department, E. H. Hansen, Sound Director"
# "Warner Bros. Studio Sound Department, Nathan Levinson, Sound Director"
# United States Department of Agriculture
# RKO Radio
# "Warner Bros. Studio Sound Department, Nathan Levinson, Sound Director"
# "Universal Studio Sound Department, Bernard B. Brown, Sound Director"
# "Walt Disney Studio Sound Department, Sam Slyfield, Sound Director"
# "Republic Studio Sound Department, Daniel Bloomberg, Sound Director"
# "Sound Service, Inc., Jack Whitney, Sound Director"
# "Sound Service, Inc., Jack Whitney, Sound Director"
# "RCA Sound, James Fields, Sound Director"
# "RCA Sound, James Fields, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Douglas Shearer, Sound Director"
# "RKO Radio Studio Sound Department, Steve Dunn, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Thomas T. Moulton, Sound Director"
# "Paramount Studio Sound Department, Loren Ryder, Sound Director"
# "20th Century-Fox Studio Sound Department, E. H. Hansen, Sound Director"
# "Columbia Studio Sound Department, John Livadary, Sound Director"
# RKO Radio
# "General Service Sound Department, Jack Whitney, Sound Director"
# "Universal Studio Sound Department, Bernard B. Brown, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Thomas T. Moulton, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Douglas Shearer, Sound Director"
# "RKO Radio Studio Sound Department, John Aalberg, Sound Director"
# "Republic Studio Sound Department, Charles Lootens, Sound Director"
# "20th Century-Fox Studio Sound Department, E. H. Hansen, Sound Director"
# "Columbia Studio Sound Department, John Livadary, Sound Director"
# "Warner Bros. Studio Sound Department, Nathan Levinson, Sound Director"
# "Paramount Studio Sound Department, Loren Ryder, Sound Director"
# "Hal Roach Studio Sound Department, Elmer Raguse, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Douglas Shearer, Sound Director"
# Walter Wanger (production company)
# RKO Radio
# Sol Lesser (production company)
# RKO Radio
# "Republic Studio Sound Department, Charles L. Lootens, Sound Director"
# "Hal Roach Studio Sound Department, Elmer A. Raguse, Sound Director"
# "20th Century-Fox Studio Sound Department, E. H. Hansen, Sound Director"
# "General Service Sound Department, Jack Whitney, Sound Director"
# "RKO Radio Studio Sound Department, John Aalberg, Sound Director"
# "Paramount Studio Sound Department, Loren L. Ryder, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Thomas T. Moulton, Sound Director"
# "Warner Bros. Studio Sound Department, Nathan Levinson, Sound Director"
# "Universal Studio Sound Department, Bernard B. Brown, Sound Director"
# "Columbia Studio Sound Department, John Livadary, Sound Director"
# Walter Wanger (production company)
# RKO Radio
# Sol Lesser (production company)
# RKO Radio
# "Metro-Goldwyn-Mayer Studio Sound Department, Douglas Shearer, Sound Director"
# "Republic Studio Sound Department, Charles L. Lootens, Sound Director"
# "Hal Roach Studio Sound Department, Elmer A. Raguse, Sound Director"
# "20th Century-Fox Studio Sound Department, E. H. Hansen, Sound Director"
# "General Service Sound Department, Jack Whitney, Sound Director"
# "RKO Radio Studio Sound Department, John Aalberg, Sound Director"
# "Paramount Studio Sound Department, Loren L. Ryder, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Thomas T. Moulton, Sound Director"
# "Warner Bros. Studio Sound Department, Nathan Levinson, Sound Director"
# "Universal Studio Sound Department, Bernard B. Brown, Sound Director"
# "Columbia Studio Sound Department, John Livadary, Sound Director"
# RKO Radio
# Hal Roach (production company)
# Walter Wanger (production company)
# RKO Radio
# RKO Radio
# "Universal Studio Sound Department, Bernard B. Brown, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Douglas Shearer, Sound Director"
# "Samuel Goldwyn Studio Sound Department, Thomas T. Moulton, Sound Director"
# "Denham Studio Sound Department, A. W. Watkins, Sound Director"
# "Paramount Studio Sound Department, Loren L. Ryder, Sound Director"
# "RKO Radio Studio Sound Department, John Aalberg, Sound Director"
# "Republic Studio Sound Department, Charles L. Lootens, Sound Director"
# "Columbia Studio Sound Department, John Livadary, Sound Director"
# "Hal Roach Studio Sound Department, Elmer A. Raguse, Sound Director"
# "Warner Bros. Studio Sound Department, Nathan Levinson, Sound Director"
# "20th Century-Fox Studio Sound Department, E. H. Hansen, Sound Director"
# Douglas Fairbanks (Commemorative Award) - recognizing the unique and outstanding contribution of Douglas Fairbanks
# "United Artists Studio Sound Department, Thomas T. Moulton, Sound Director"
# "Republic Studio Sound Department, Charles L. Lootens, Sound Director"
# "Warner Bros. Studio Sound Department, Nathan Levinson, Sound Director"
# "Paramount Studio Sound Department, Loren L. Ryder, Sound Director"
# "Hal Roach Studio Sound Department, Elmer A. Raguse, Sound Director"
# "20th Century-Fox Studio Sound Department, Edmund H. Hansen, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Douglas Shearer, Sound Director"
# "Universal Studio Sound Department, Bernard B. Brown, Sound Director"
# "RKO Radio Studio Sound Department, John Aalberg, Sound Director"
# "Columbia Studio Sound Department, John Livadary, Sound Director"
# RKO Radio
# RKO Radio
# RKO Radio
# "United Artists Studio Sound Department, Thomas T. Moulton, Sound Director"
# "Grand National Studio Sound Department, A. E. Kaye, Sound Director"
# "RKO Radio Studio Sound Department, John Aalberg, Sound Director"
# "20th Century-Fox Studio Sound Department, E. H. Hansen, Sound Director"
# "Warner Bros. Studio Sound Department, Nathan Levinson, Sound Director"
# "Columbia Studio Sound Department, John Livadary, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Douglas Shearer, Sound Director"
# "Universal Studio Sound Department, Homer G. Tasker, Sound Director"
# "Hal Roach Studio Sound Department, Elmer A. Raguse, Sound Director"
# "Paramount Studio Sound Department, Loren L. Ryder, Sound Director"
# RKO Radio
# "Metro-Goldwyn-Mayer Studio Sound Department, Douglas Shearer, Sound Director"
# "20th Century-Fox Studio Sound Department, E. H. Hansen, Sound Director"
# "Warner Bros. Studio Sound Department, Nathan Levinson, Sound Director"
# "United Artists Studio Sound Department, Thomas T. Moulton, Sound Director"
# "Hal Roach Studio Sound Department, Elmer A. Raguse, Sound Director"
# "Columbia Studio Sound Department, John Livadary, Sound Director"
# "Paramount Studio Sound Department, Franklin B. Hansen, Sound Director"
# "RKO Radio Studio Sound Department, J. O. Aalberg, Sound Director"
# "Universal Studio Sound Department, Homer G. Tasker, Sound Director"
# RKO Radio
# RKO Radio
# RKO Radio
# "Metro-Goldwyn-Mayer Studio Sound Department, Douglas Shearer, Sound Director"
# "Universal Studio Sound Department, Gilbert Kurland, Sound Director"
# "Warner Bros.-First National Studio Sound Department, Nathan Levinson, Sound Director"
# "United Artists Studio Sound Department, Thomas T. Moulton, Sound Director"
# "RKO Radio Studio Sound Department, Carl Dreher, Sound Director"
# "Paramount Studio Sound Department, Franklin B. Hansen, Sound Director"
# "Columbia Studio Sound Department, John Livadary, Sound Director"
# Republic Studio Sound Department
# "20th Century-Fox Studio Sound Department, E. H. Hansen, Sound Director"
# RKO Radio
# Jesse L. Lasky (production company)
# "Columbia Studio Sound Department, John Livadary, Sound Director"
# "United Artists Studio Sound Department, Thomas T. Moulton, Sound Director"
# "Paramount Studio Sound Department, Franklin B. Hansen, Sound Director"
# "Warner Bros.-First National Studio Sound Department, Nathan Levinson, Sound Director"
# "RKO Radio Studio Sound Department, Carl Dreher, Sound Director"
# "Universal Studio Sound Department, Theodore Soderberg, Sound Director"
# "Metro-Goldwyn-Mayer Studio Sound Department, Douglas Shearer, Sound Director"
# "Fox Studio Sound Department, E. H. Hansen, Sound Director"
# William Tummel (Fox)
# Charles Dorian (Metro-Goldwyn-Mayer)
# Charles Barton (Paramount)
# Dewey Starkey (RKO Radio)
# Fred Fox (United Artists)
# Scott Beal (Universal)
# Gordon Hollingshead (Warner Bros.)
# Percy Ikerd (Fox)
# Bunny Dull (Metro-Goldwyn-Mayer)
# John S. Waters (Metro-Goldwyn-Mayer)
# Sidney S. Brod (Paramount)
# Arthur Jacobson (Paramount)
# Eddie Killey (RKO Radio)
# Benjamin Silvey (United Artists)
# Joe McDonough (Universal)
# W. J. Reiter (Universal)
# Frank X. Shaw (Warner Bros.)
# RKO Radio
# "Paramount Studio Sound Department, Franklin B. Hansen, Sound Director"
# "Warner Bros. Studio Sound Department, Nathan Levinson, Sound Director"
# "Warner Bros. Studio Sound Department, Nathan Levinson, Sound Director"
# "Warner Bros. Studio Sound Department, Nathan Levinson, Sound Director"
# RKO Radio
# RKO Radio
# Paramount Publix Studio Sound Department
# Metro-Goldwyn-Mayer Studio Sound Department
# RKO Radio Studio Sound Department
# Warner Bros.-First National Studio Sound Department
# RKO Radio
# Paramount Publix Studio Sound Department
# Samuel Goldwyn - United Artists Studio Sound Department
# Metro-Goldwyn-Mayer Studio Sound Department
# RKO Radio Studio Sound Department
# "Metro-Goldwyn-Mayer Studio Sound Department, Douglas Shearer, Sound Director"
# "(RKO Radio Studio Sound Department, John Tribby, Sound Director)"
# "(Paramount Famous Lasky Studio Sound Department, Franklin Hansen, Sound Director)"
# "(United Artists Studio Sound Department, Oscar Lagerstrom, Sound Director)"
# "(First National Studio Sound Department, George Groves, Sound Director)"
# """).strip("\n")
#
#
#
#
# lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
# df_ = pd.DataFrame({"original": lines})
# df = df_.copy()
# df["clean"] = df["original"].str.strip().str.strip('"')
#
# matched = df["clean"].str.extractall(pat_sd_segment)
# if not matched.empty:
#     matched = matched.reset_index().rename(columns={"level_0": "row_id", "match": "segment_id"})
#     for col in ["affiliation", "person", "role"]:
#         matched[col] = matched[col].str.strip()
# else:
#     matched = pd.DataFrame(columns=["row_id", "segment_id", "affiliation", "person", "role"])
#
# rows_with_match = set(matched["row_id"].unique().tolist())
# df["has_person_role"] = df.index.isin(rows_with_match)
#
# no_match_mask = ~df["has_person_role"]
# affil_only = df.loc[no_match_mask, "clean"].str.extract(affil_only_pat)
# affil_only = affil_only.rename(columns={0: "affiliation"})
# affil_only = affil_only.join(df.loc[no_match_mask].reset_index().rename(columns={"index":"row_id"}))
# affil_only = affil_only.dropna(subset=["affiliation"])
# if not affil_only.empty:
#     affil_only["affiliation"] = affil_only["affiliation"].str.strip()
# person_affil_parentheses = df_['original'].str.extractall(pat_sound_parentheses).reset_index().rename(columns={"level_0":"row_id"})
# print(person_affil_parentheses)
# covered_rows = set(rows_with_match) | set(affil_only["row_id"].tolist())
# unmatched = df.loc[~df.index.isin(covered_rows)].copy()
#
# matched.to_csv('../../transformed/sd_pattern_matched_test.csv', index=False,quoting=csv.QUOTE_ALL)
# affil_only.to_csv('../../transformed/sd_pattern_affiliated_test.csv', index=False,quoting=csv.QUOTE_ALL)
# unmatched["original"].to_csv('../../transformed/sd_pattern_unmatched_test.csv', index=False,quoting=csv.QUOTE_ALL)
# person_affil_parentheses.to_csv("../../test_person_affiliation_parentheses.csv")
# summary = pd.DataFrame({
#     "total_rows":[len(df)],
#     "with_person_role":[len(rows_with_match)],
#     "affiliation_only":[len(affil_only) if not affil_only.empty else 0],
#     "unmatched":[len(unmatched)]
# })
#
# print("Summary (Sound Director parsing)", summary)
# print("Matched segments (affiliation, person, role) — preview", matched[:])
# print("Affiliation-only (fallback) — preview", affil_only[:])
# print("Parenthesis-only", person_affil_parentheses[:])
# print("Unmatched lines — preview", unmatched[:])
# samples = [
#   'Music and Lyric by Leslie Odom, Jr. and Sam Ashworth - "One Night in Miami..."',
#   'Music by Elton John; Lyric by Bernie Taupin - "Rocketman"',
#   'Screenplay by Will Berson & Shaka King; Story by Will Berson & Shaka King and Kenny Lucas & Keith Lucas - "Judas and the Black Messiah"',
# ]
#
# for s in samples:
#     print('---', s)
#     for m in RegexPatterns.Studio.pat_by_paren.finditer(s):
#         print('BY:', m.group('role'), '->', m.group('entity'))
#     for m in RegexPatterns.Screenplay.pattern_written.finditer(s):
#         role = m.group('role') or m.group('role2')
#         ent  = m.group('entity') or m.group('entity2')
#         print('WR:', role, '->', ent)
df = pd.read_csv('../../transformed/golden_version.csv')

df.quantile()
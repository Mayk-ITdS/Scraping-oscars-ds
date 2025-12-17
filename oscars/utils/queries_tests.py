import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "transformed" / "role_oscars_gold.db"
def ask_my_base():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    sql = """
    SELECT
        e.name        AS entity_name,
        e.entity_type,
        ce.year       AS ceremony_year,
        c.name,
        f.title       AS film_title,
        n.is_winner
    FROM roles r
    JOIN entities   e  ON r.entity_id    = e.entity_id
    JOIN nominations n ON r.nomination_id = n.nomination_id
    JOIN categories c  ON n.category_id   = c.category_id
    JOIN ceremonies ce ON n.ceremony_id   = ce.ceremony_id
    LEFT JOIN films f  ON n.film_id       = f.film_id
    WHERE
        e.entity_type <> 'person'
        AND c.name = ?
    ORDER BY
        ce.year,
        film_title,
        entity_name;
    """

    rows = cur.execute(sql, ("MUSIC (Original Score)",)).fetchall()
    for row in rows:
        print(row)

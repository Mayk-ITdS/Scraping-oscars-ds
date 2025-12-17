

def create_schema(conn):
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ceremonies (
            ceremony_id INTEGER PRIMARY KEY,
            year        INTEGER NOT NULL UNIQUE
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY,
            name        TEXT NOT NULL UNIQUE
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS films (
            film_id INTEGER PRIMARY KEY,
            title   TEXT NOT NULL,
            year    INTEGER,
            UNIQUE(title, year)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS entities (
            entity_id   INTEGER PRIMARY KEY,
            name        TEXT NOT NULL,
            entity_type TEXT,
            gender      TEXT,
            UNIQUE(name, entity_type)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS nominations (
            nomination_id INTEGER PRIMARY KEY,
            ceremony_id   INTEGER NOT NULL,
            category_id   INTEGER NOT NULL,
            film_id       INTEGER,
            is_winner     INTEGER NOT NULL DEFAULT 0,
            role          TEXT,
            note          TEXT,
            FOREIGN KEY (ceremony_id) REFERENCES ceremonies(ceremony_id),
            FOREIGN KEY (category_id) REFERENCES categories(category_id),
            FOREIGN KEY (film_id)     REFERENCES films(film_id)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS roles (
            role_id        INTEGER PRIMARY KEY,
            nomination_id  INTEGER NOT NULL,
            entity_id      INTEGER NOT NULL,
            role_function  TEXT,
            role_subtype   TEXT,
            FOREIGN KEY (nomination_id) REFERENCES nominations(nomination_id),
            FOREIGN KEY (entity_id)     REFERENCES entities(entity_id)
        );
    """)

    conn.commit()

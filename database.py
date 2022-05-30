import psycopg2
import bulletin_config
import time
import bulletin_config
import datetime
import utilities


def connection():
    return psycopg2.connect(
        host=bulletin_config.DATABASE_HOST,
        port=bulletin_config.DATABASE_PORT,
        database=bulletin_config.DATABASE_NAME,
        user=bulletin_config.DATABASE_USER,
        password=bulletin_config.DATABASE_PASSWORD)


def get_items_for_user(user_id: list[str], limit: int = 500, offset: int = 0):
    conn = connection()
    cur = conn.cursor()
    cur.execute(
        'SELECT "id", last_edit, title, notes, "owner" ' +
        'FROM "bulletin-2".items ' +
        'WHERE "owner" = ANY(%s) ORDER BY "last_edit" DESC LIMIT %s OFFSET %s',
        (user_id, limit, offset)
    )
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [{
        "id": item[0],
        "last_edit": item[1],
        "title": item[2],
        "notes": item[3],
        "owner": item[4],
    } for item in results]
# SELECT "id", last_edit, title, notes, "owner"
# FROM "bulletin-2".items
# WHERE "owner" = ANY('{1,2}') ORDER BY "last_edit" DESC LIMIT 100 OFFSET 0;


def fetch_item(item_id):
    conn = connection()
    cur = conn.cursor()
    cur.execute(
        'SELECT "id", notes, last_edit, title, content, grades, "owner" ' +
        'FROM "bulletin-2".items ' +
        'WHERE "id" = %s',
        (item_id,)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    return {
        "id": result[0],
        "notes": result[1],
        "last_edit": result[2],
        "title": result[3],
        "content": result[4],
        "grades": result[5],
        "owner": result[6],
    }


def fetch_bulletins(limit: int = 500, offset: int = 0, earlier_than: datetime.date = None):
    conn = connection()
    cur = conn.cursor()
    if earlier_than:
        cur.execute(
            'SELECT distinct("date") FROM "bulletin-2".occurrences ' +
            'WHERE date <= %s::timestamp ORDER BY "date" DESC LIMIT %s OFFSET %s',
            (earlier_than.strftime("%Y-%m-%d"), limit, offset)
        )
    else:
        cur.execute(
            'SELECT distinct("date") FROM "bulletin-2".occurrences ' +
            'ORDER BY "date" DESC LIMIT %s OFFSET %s',
            (limit, offset)
        )
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


def fetch_items_for_day(date: datetime.date):
    conn = connection()
    cur = conn.cursor()
    cur.execute('SELECT distinct on ("bulletin-2".items.id) "bulletin-2".items.id, "bulletin-2".items.title, "bulletin-2".items."content", "bulletin-2".items.grades ' +
                'FROM "bulletin-2".occurrences, "bulletin-2".items ' +
                'WHERE "bulletin-2".occurrences."date" = %s::timestamp ' +
                'AND "bulletin-2".occurrences."item" = "bulletin-2".items.id',
                (date.strftime("%Y-%m-%d"),)
                )
    results = cur.fetchall()
    cur.close()
    conn.close()
    return [{
        "id": item[0],
        "title": item[1],
        "content": item[2],
        "grades": item[3],
        "grades_string": utilities.grades_string(item[3]),
    } for item in results]


def update_item(item_id, title, content, notes, grades):
    conn = connection()
    cur = conn.cursor()
    cur.execute(
        'UPDATE "bulletin-2".items ' +
        'SET title = %s, content = %s, notes = %s, grades = %s, "last_edit" = %s ' +
        'WHERE "id" = %s',
        (title, content, notes, grades, int(time.time()), item_id)
    )
    conn.commit()
    cur.close()
    conn.close()

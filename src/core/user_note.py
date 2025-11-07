import sqlite3
from typing import Optional, List, Tuple, Dict


TABLE_USER_NOTE = "user_note"


def ensure_user_note_table(conn: sqlite3.Connection) -> None:
    """保证 user_note 表存在。"""
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_USER_NOTE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL UNIQUE,
                hiragana TEXT,
                meaning TEXT,
                lesson TEXT,
                wrong_count INTEGER NOT NULL DEFAULT 1,
                last_wrong_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()
    finally:
        cursor.close()


def record_wrong_answer(
    conn: sqlite3.Connection,
    word: str,
    hiragana: Optional[str],
    meaning: Optional[str],
    lesson: Optional[str],
) -> None:
    """将做错的单词插入/更新到 user_note 表。"""
    ensure_user_note_table(conn)
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"""
            INSERT INTO {TABLE_USER_NOTE} (word, hiragana, meaning, lesson, wrong_count, last_wrong_at)
            VALUES (?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(word) DO UPDATE SET
                hiragana = excluded.hiragana,
                meaning = excluded.meaning,
                lesson = excluded.lesson,
                wrong_count = {TABLE_USER_NOTE}.wrong_count + 1,
                last_wrong_at = CURRENT_TIMESTAMP;
            """,
            (word, hiragana, meaning, lesson),
        )
        conn.commit()
    finally:
        cursor.close()


def fetch_user_notes(conn: sqlite3.Connection) -> List[Tuple[str, Optional[str], Optional[str], Optional[str], int, str]]:
    """查询收藏（错题）列表，按最近错误时间倒序。"""
    ensure_user_note_table(conn)
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"SELECT word, hiragana, meaning, lesson, wrong_count, last_wrong_at FROM {TABLE_USER_NOTE} ORDER BY last_wrong_at DESC;"
        )
        return cursor.fetchall()
    finally:
        cursor.close()


def delete_user_note(conn: sqlite3.Connection, word: str) -> bool:
    """删除指定单词的收藏记录。"""
    ensure_user_note_table(conn)
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"DELETE FROM {TABLE_USER_NOTE} WHERE word = ?;",
            (word,),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()


def record_wrong_word(conn: sqlite3.Connection, word: str) -> None:
    """从 vocabulary 查找信息并写入错题本。"""
    ensure_user_note_table(conn)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT word, hiragana, meaning, lesson FROM vocabulary WHERE word = ? LIMIT 1;",
            (word,),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()

    if row:
        _, hira, meaning, lesson = row
        record_wrong_answer(conn, word, hira, meaning, lesson)
    else:
        record_wrong_answer(conn, word, None, None, None)



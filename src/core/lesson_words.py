import sqlite3
import re
from typing import List, Tuple, Union

TABLE_VOCABULARY = "vocabulary"


def get_lessons(conn: sqlite3.Connection) -> List[str]:
    """获取所有存在单词的课次列表，并按数字顺序从第1课到第48课排序。"""
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT DISTINCT lesson FROM {TABLE_VOCABULARY} WHERE lesson IS NOT NULL AND TRIM(lesson) != '';"
        )
        rows = [r[0] for r in cursor.fetchall() if r and r[0]]

        pattern = re.compile(r"第(\d+)课")
        numbered = []
        for label in rows:
            m = pattern.fullmatch(label.strip())
            if not m:
                continue
            num = int(m.group(1))
            if 1 <= num <= 48:
                numbered.append((num, label))

        # 去重并按数字排序
        dedup = {}
        for num, label in numbered:
            dedup[num] = label
        ordered = [dedup[n] for n in sorted(dedup.keys())]
        return ordered
    finally:
        if cursor:
            cursor.close()


def _normalize_lessons(lesson_input: Union[str, List[str]]) -> Union[str, List[str]]:
    """统一化课次参数：支持 all / 单值字符串 / 列表。"""
    if isinstance(lesson_input, list):
        return [str(x) for x in lesson_input if str(x).strip()]
    s = (lesson_input or "").strip()
    if not s:
        return "all"
    return s


def get_words_by_lessons(
    conn: sqlite3.Connection,
    lesson_input: Union[str, List[str]] = "all",
) -> List[Tuple[str, str, str, str]]:
    """按课次查询单词。

    返回 (word, hiragana, meaning, lesson) 列表。
    lesson_input 可为："all" / "第3课" / ["第1课","第2课"]。
    """
    lesson_norm = _normalize_lessons(lesson_input)
    cursor = None
    try:
        cursor = conn.cursor()
        if lesson_norm == "all":
            sql = f"SELECT word, hiragana, meaning, lesson FROM {TABLE_VOCABULARY} ORDER BY lesson ASC, rowid ASC;"
            cursor.execute(sql)
        elif isinstance(lesson_norm, list):
            placeholders = ",".join(["?"] * len(lesson_norm))
            sql = f"SELECT word, hiragana, meaning, lesson FROM {TABLE_VOCABULARY} WHERE lesson IN ({placeholders}) ORDER BY lesson ASC, rowid ASC;"
            cursor.execute(sql, tuple(lesson_norm))
        else:
            sql = f"SELECT word, hiragana, meaning, lesson FROM {TABLE_VOCABULARY} WHERE lesson = ? ORDER BY rowid ASC;"
            cursor.execute(sql, (lesson_norm,))
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()



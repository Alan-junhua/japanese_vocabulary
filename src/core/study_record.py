import sqlite3
from typing import List, Tuple


TABLE_STUDY_RECORDS = "study_records"


def ensure_study_records_table(conn: sqlite3.Connection) -> None:
    """保证 study_records 表存在。"""
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE_STUDY_RECORDS} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL,
                is_correct INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        # 创建索引以提高查询性能
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_created_at ON {TABLE_STUDY_RECORDS}(created_at);"
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_word ON {TABLE_STUDY_RECORDS}(word);"
        )
        conn.commit()
    finally:
        cursor.close()


def record_study(conn: sqlite3.Connection, word: str, is_correct: bool) -> None:
    """记录学习记录。"""
    ensure_study_records_table(conn)
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"""
            INSERT INTO {TABLE_STUDY_RECORDS} (word, is_correct, created_at)
            VALUES (?, ?, CURRENT_TIMESTAMP);
            """,
            (word, 1 if is_correct else 0),
        )
        conn.commit()
    finally:
        cursor.close()


def get_today_stats(conn: sqlite3.Connection) -> Tuple[int, float]:
    """获取今日学习统计。
    
    返回 (总题数, 正确率)
    正确率范围: 0.0 - 100.0
    """
    ensure_study_records_table(conn)
    cursor = conn.cursor()
    try:
        # 查询今日的记录（使用日期比较）
        cursor.execute(
            f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_count
            FROM {TABLE_STUDY_RECORDS}
            WHERE DATE(created_at) = DATE('now', 'localtime');
            """
        )
        row = cursor.fetchone()
        total = row[0] if row and row[0] else 0
        correct_count = row[1] if row and row[1] else 0
        
        # 计算正确率
        accuracy = (correct_count / total * 100) if total > 0 else 0.0
        
        return total, round(accuracy, 1)
    finally:
        cursor.close()


def record_study_batch(conn: sqlite3.Connection, records: List[Tuple[str, bool]]) -> None:
    """批量记录学习记录。"""
    if not records:
        return
    
    ensure_study_records_table(conn)
    cursor = conn.cursor()
    try:
        cursor.executemany(
            f"""
            INSERT INTO {TABLE_STUDY_RECORDS} (word, is_correct, created_at)
            VALUES (?, ?, CURRENT_TIMESTAMP);
            """,
            [(word, 1 if is_correct else 0) for word, is_correct in records],
        )
        conn.commit()
    finally:
        cursor.close()


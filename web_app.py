from flask import Flask, render_template, request, jsonify
import sqlite3
from typing import List, Tuple, Union
import os
import sys

# 计算工程根目录并修正模块搜索路径，防止导入失败
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 复用现有核心逻辑
from src.core.random_kana import SQLiteDB, generate_question
from src.core.lesson_words import get_lessons, get_words_by_lessons
from src.core.user_note import (
    ensure_user_note_table,
    fetch_user_notes,
    delete_user_note,
    record_wrong_word,
)


app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static"),
    static_url_path="/static",
)

# 中文 JSON 直出，不转义
app.config["JSON_AS_ASCII"] = False


def get_sqlite_connection() -> sqlite3.Connection:
    db_path = os.path.join(BASE_DIR, "japanese_learning.db")
    return sqlite3.connect(db_path)


def parse_lesson_param(inp: str) -> Union[str, List[str]]:
    if not inp:
        return "all"
    s = inp.strip().lower()
    if s == "all":
        return "all"
    if s.isdigit():
        num = int(s)
        if 1 <= num <= 48:
            return f"第{num}课"
        return "all"
    if "-" in s:
        parts = s.split("-")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            start, end = int(parts[0]), int(parts[1])
            if 1 <= start <= end <= 48:
                return [f"第{i}课" for i in range(start, end + 1)]
    return "all"


@app.route("/healthz")
def healthz():
    try:
        # 仅检查数据库文件是否存在；不强制连接
        db_path = os.path.join(BASE_DIR, "japanese_learning.db")
        return jsonify({"ok": True, "dbExists": os.path.exists(db_path)})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/search", methods=["GET"])
def search_page():
    return render_template("search.html")


@app.route("/quiz", methods=["GET"])
def quiz_page():
    return render_template("quiz.html")


@app.route("/lessons", methods=["GET"])
def lessons_page():
    return render_template("lessons.html")


@app.route("/notes", methods=["GET"])
def notes_page():
    return render_template("user_notes.html")


@app.route("/api/search", methods=["POST"]) 
def api_search():
    data = request.get_json(silent=True) or request.form
    query_type = (data.get("type") or "jp").strip()
    keyword = (data.get("keyword") or "").strip()

    if not keyword:
        return jsonify({"ok": False, "message": "关键词不能为空"}), 400

    try:
        conn = get_sqlite_connection()
        cur = conn.cursor()
        if query_type == "jp":
            cur.execute(
                "SELECT word, hiragana, meaning, lesson FROM vocabulary WHERE word LIKE ?",
                (f"%{keyword}%",),
            )
        else:
            cur.execute(
                "SELECT word, hiragana, meaning, lesson FROM vocabulary WHERE meaning LIKE ?",
                (f"%{keyword}%",),
            )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        results = [
            {
                "word": r[0],
                "hiragana": r[1],
                "meaning": r[2],
                "lesson": r[3],
            }
            for r in rows
        ]
        return jsonify({"ok": True, "results": results})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


@app.route("/api/quiz", methods=["POST"]) 
def api_quiz():
    data = request.get_json(silent=True) or request.form
    lesson_raw = (data.get("lesson") or "all").strip()
    count_raw = (data.get("count") or "10").strip()

    try:
        count = int(count_raw)
        count = max(1, min(count, 50))
    except ValueError:
        count = 10

    lesson_pattern = parse_lesson_param(lesson_raw)

    questions = []
    try:
        db = SQLiteDB()
        with db as conn:
            all_valid_words: List[Tuple[str, str]] = SQLiteDB.query_valid_words(conn, lesson_pattern)
            if not all_valid_words:
                return jsonify({"ok": False, "message": "未找到可用单词"}), 200

            # 打乱并尽力生成指定数量的题目
            import random
            random.shuffle(all_valid_words)

            for word, hira in all_valid_words:
                if len(questions) >= count:
                    break
                q = generate_question(conn, word, hira)
                if not q:
                    continue
                # 将正确答案隐藏为索引，避免明文传输
                opts = q["options"]
                correct_index = opts.index(q["correct"]) if q["correct"] in opts else 0
                questions.append({
                    "word": q["word"],
                    "options": opts,
                    "correctIndex": correct_index,
                })

        return jsonify({"ok": True, "questions": questions})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


@app.route("/api/quiz/wrong", methods=["POST"])
def api_quiz_wrong():
    data = request.get_json(silent=True) or request.form
    word = (data.get("word") or "").strip()
    if not word:
        return jsonify({"ok": False, "message": "单词不能为空"}), 400
    try:
        conn = get_sqlite_connection()
        record_wrong_word(conn, word)
        conn.close()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


@app.route("/api/lessons", methods=["GET"]) 
def api_lessons():
    try:
        conn = get_sqlite_connection()
        lessons = get_lessons(conn)
        conn.close()
        return jsonify({"ok": True, "lessons": lessons})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


@app.route("/api/user_notes", methods=["GET"])
def api_user_notes():
    try:
        conn = get_sqlite_connection()
        ensure_user_note_table(conn)
        rows = fetch_user_notes(conn)
        conn.close()
        notes = [
            {
                "word": r[0],
                "hiragana": r[1],
                "meaning": r[2],
                "lesson": r[3],
                "wrongCount": r[4],
                "lastWrongAt": r[5],
            }
            for r in rows
        ]
        return jsonify({"ok": True, "notes": notes})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


@app.route("/api/user_notes/delete", methods=["POST"])
def api_user_notes_delete():
    data = request.get_json(silent=True) or request.form
    word = (data.get("word") or "").strip()
    if not word:
        return jsonify({"ok": False, "message": "单词不能为空"}), 400
    try:
        conn = get_sqlite_connection()
        deleted = delete_user_note(conn, word)
        conn.close()
        if not deleted:
            return jsonify({"ok": False, "message": "未找到记录"}), 404
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


@app.route("/api/lesson_words", methods=["POST"]) 
def api_lesson_words():
    data = request.get_json(silent=True) or request.form
    lesson = (data.get("lesson") or "all").strip()
    try:
        conn = get_sqlite_connection()
        rows = get_words_by_lessons(conn, lesson)
        conn.close()
        results = [
            {"word": r[0], "hiragana": r[1], "meaning": r[2], "lesson": r[3]}
            for r in rows
        ]
        return jsonify({"ok": True, "results": results})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500


@app.errorhandler(404)
def handle_404(_):
    return render_template("index.html"), 404


@app.errorhandler(500)
def handle_500(e):
    return jsonify({"ok": False, "message": f"服务器错误: {e}"}), 500


if __name__ == "__main__":
    # 启动：python web_app.py
    port = int(os.environ.get("PORT", "5000"))
    # 为避免用户复制 0.0.0.0 导致无法直接在浏览器访问，改为本机 127.0.0.1
    app.run(host="127.0.0.1", port=port, debug=True)



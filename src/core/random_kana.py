import sqlite3
from sqlite3 import Error
import os
import random

# ------------------- 全局配置（工具逻辑依赖，需保留在此）-------------------
DEBUG_MODE = True
DEFAULT_WRONG_OPTION_COUNT = 3  # 错误选项需满足此数量才视为有效题
MAX_ATTEMPT_GENERATE_WRONG = 20
TABLE_VOCABULARY = "vocabulary"
TABLE_KANA = "japanese_kana"
VALID_HIRAGANA_CONDITION = "hiragana IS NOT NULL AND TRIM(hiragana) != ''"


# ------------------- 数据库工具类 -------------------
class SQLiteDB:
    def __init__(self, db_name="japanese_learning.db"):
        self.db_path = os.path.join(os.getcwd(), db_name)
        self.connection = None

    def __enter__(self):
        if DEBUG_MODE:
            print(f"\n【数据库调试】工作目录：{os.getcwd()}")
            print(f"【数据库调试】数据库路径：{self.db_path}")
            print(f"【数据库调试】文件存在：{os.path.exists(self.db_path)}")
        
        try:
            self.connection = sqlite3.connect(self.db_path)
            if DEBUG_MODE:
                print("【数据库调试】连接成功")
            return self.connection
        except Error as e:
            print(f"❌ 数据库连接失败：{e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.close()
            if DEBUG_MODE:
                print("【数据库调试】连接已关闭")
        if exc_type:
            print(f"❌ 数据库异常：{exc_val}")

    @staticmethod
    def query_valid_words(conn, lesson_pattern):
        """查询所有带有效平假名的单词（供外部筛选有效题）"""
        cursor = None
        try:
            cursor = conn.cursor()

            # 调试：打印课程分布（前10个）
            if DEBUG_MODE:
                print("\n【关键调试】课程单词分布（前10个）：")
                cursor.execute(f"SELECT lesson, COUNT(*) FROM {TABLE_VOCABULARY} GROUP BY lesson LIMIT 10;")
                for lesson, count in cursor.fetchall():
                    print(f"  → {lesson}：{count}个单词")
                print("  → ...（仅显示前10个课程）")

            # 动态生成查询SQL
            if lesson_pattern == "all":
                sql = f"SELECT word, hiragana FROM {TABLE_VOCABULARY} WHERE {VALID_HIRAGANA_CONDITION}"
                params = ()
            elif isinstance(lesson_pattern, list):
                placeholders = ",".join(["?"] * len(lesson_pattern))
                sql = f"SELECT word, hiragana FROM {TABLE_VOCABULARY} WHERE lesson IN ({placeholders}) AND {VALID_HIRAGANA_CONDITION}"
                params = lesson_pattern
            else:
                sql = f"SELECT word, hiragana FROM {TABLE_VOCABULARY} WHERE lesson = ? AND {VALID_HIRAGANA_CONDITION}"
                params = (lesson_pattern,)

            # 执行查询
            if DEBUG_MODE:
                print(f"\n【查询调试】SQL：{sql}")
                print(f"【查询调试】参数：{params[:5]}..." if isinstance(params, list) else params)
            cursor.execute(sql, params)
            valid_words = cursor.fetchall()
            print(f"\n【查询结果】共找到 {len(valid_words)} 个带平假名的单词（后续筛选有效题）")
            return valid_words

        except Error as e:
            print(f"❌ 单词查询失败：{e}")
            return []
        finally:
            if cursor:
                cursor.close()


# ------------------- 核心业务工具函数 -------------------
def get_modifiable_positions(group_id_list):
    """筛选可修改的字符位置（内部工具，不对外暴露也可）"""
    return [idx for idx, gid in enumerate(group_id_list) if gid and gid != 0]


def modify_single_position(conn, current_char, current_gid):
    """单个字符错误替换（内部工具）"""
    cursor = None
    try:
        cursor = conn.cursor()
        sql = f"SELECT kana FROM {TABLE_KANA} WHERE confusion_group_id = ? AND kana != ? LIMIT 10;"
        cursor.execute(sql, (current_gid, current_char))
        candidates = [item[0] for item in cursor.fetchall() if item[0]]

        if not candidates:
            return None, "无匹配错误字符"
        target_char = random.choice(candidates)
        return target_char, f"「{current_char}」→「{target_char}」"
    except Error as e:
        return None, f"字符修改失败：{e}"
    finally:
        if cursor:
            cursor.close()


def generate_wrong_options(conn, original_hira):
    """生成足够数量的错误选项（对外提供：返回(错误选项列表, 是否有效)）"""
    if not original_hira:
        return [], False

    # 1. 获取平假名对应的group_id
    cursor = None
    try:
        cursor = conn.cursor()
        placeholders = ",".join(["?"] * len(original_hira))
        sql = f"SELECT kana, confusion_group_id FROM {TABLE_KANA} WHERE kana IN ({placeholders})"
        cursor.execute(sql, tuple(original_hira))
        kana_gid_map = dict(cursor.fetchall())
        group_ids = [kana_gid_map.get(c) for c in original_hira]
    except Error as e:
        print(f"❌ 获取group_id失败：{e}")
        return [], False
    finally:
        if cursor:
            cursor.close()

    # 2. 生成错误选项（需满足数量+去重）
    wrong_opts = set()
    attempt = 0
    original_chars = list(original_hira)

    while len(wrong_opts) < DEFAULT_WRONG_OPTION_COUNT and attempt < MAX_ATTEMPT_GENERATE_WRONG:
        attempt += 1
        modified = original_chars.copy()
        modifiable_pos = get_modifiable_positions(group_ids)

        if not modifiable_pos:
            if DEBUG_MODE:
                print(f"【调试】{original_hira}：无可用修改位置")
            break

        # 随机修改1-2个字符（避免错误离谱）
        modify_count = random.choice([1, 2]) if len(modifiable_pos) >= 2 else 1
        for pos in random.sample(modifiable_pos, modify_count):
            char = modified[pos]
            gid = group_ids[pos]
            new_char, log = modify_single_position(conn, char, gid)
            
            if not new_char:
                if DEBUG_MODE:
                    print(f"【调试】{original_hira}：修改失败（{log}）")
                break
            modified[pos] = new_char
        else:
            # 所有选中位置都修改成功
            wrong_opt = "".join(modified)
            if wrong_opt != original_hira:
                wrong_opts.add(wrong_opt)

    # 判定是否有效（满足错误选项数量）
    wrong_opts = list(wrong_opts)
    is_valid = len(wrong_opts) >= DEFAULT_WRONG_OPTION_COUNT
    if not is_valid and DEBUG_MODE:
        print(f"【调试】{original_hira}：仅生成{len(wrong_opts)}个错误选项（需{DEFAULT_WRONG_OPTION_COUNT}个），视为无效题")
    return wrong_opts, is_valid


def generate_question(conn, word, original_hira):
    """生成完整题目（对外提供：返回题目字典/None，None表示无效题）"""
    wrong_opts, is_valid = generate_wrong_options(conn, original_hira)
    if not is_valid:
        return None

    # 组合选项并打乱
    all_opts = wrong_opts + [original_hira]
    random.shuffle(all_opts)
    return {
        "word": word,
        "correct": original_hira,
        "options": all_opts
    }
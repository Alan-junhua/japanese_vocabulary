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
        # 支持PyInstaller打包后的路径处理
        import sys
        if getattr(sys, 'frozen', False):
            # 打包后的可执行文件：数据库放在可执行文件所在目录
            base_dir = os.path.dirname(sys.executable)
        else:
            # 开发环境：数据库放在当前工作目录
            base_dir = os.getcwd()
        self.db_path = os.path.join(base_dir, db_name)
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


def get_delete_positions(group_id_list):
    """筛选需要删除的字符位置（confusion_group_id == 100）"""
    return [idx for idx, gid in enumerate(group_id_list) if gid == 100]


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
    
    # 获取可删除的位置（confusion_group_id == 100）
    delete_pos = get_delete_positions(group_ids)
    # 获取可替换的位置（confusion_group_id != 0 且 != 100）
    modifiable_pos = [idx for idx, gid in enumerate(group_ids) if gid and gid != 0 and gid != 100]

    # 如果既没有可删除的也没有可替换的，直接返回
    if not delete_pos and not modifiable_pos:
        if DEBUG_MODE:
            print(f"【调试】{original_hira}：无可用修改位置")
        return [], False

    while len(wrong_opts) < DEFAULT_WRONG_OPTION_COUNT and attempt < MAX_ATTEMPT_GENERATE_WRONG:
        attempt += 1
        modified = original_chars.copy()
        modified_group_ids = group_ids.copy()
        operation_performed = False
        
        # 决定执行哪些操作
        # 如果只有删除位置，必须执行删除
        # 如果只有替换位置，必须执行替换
        # 如果两者都有，随机选择执行删除、替换或两者都执行
        if delete_pos and not modifiable_pos:
            # 只有删除位置
            do_delete = True
            do_replace = False
        elif modifiable_pos and not delete_pos:
            # 只有替换位置
            do_delete = False
            do_replace = True
        else:
            # 两者都有，随机选择
            do_delete = random.random() < 0.6
            do_replace = not do_delete or random.random() < 0.5  # 如果执行删除，50%概率也执行替换
        
        # 执行删除操作
        if do_delete and delete_pos:
            delete_count = random.choice([1, 2]) if len(delete_pos) >= 2 else 1
            positions_to_delete = random.sample(delete_pos, min(delete_count, len(delete_pos)))
            # 按从后往前删除，避免索引偏移问题
            positions_to_delete.sort(reverse=True)
            for pos in positions_to_delete:
                if pos < len(modified):
                    modified.pop(pos)
                    modified_group_ids.pop(pos)
                    operation_performed = True
            if DEBUG_MODE and operation_performed:
                deleted_chars = [original_chars[p] for p in positions_to_delete if p < len(original_chars)]
                print(f"【调试】{original_hira}：删除字符 {deleted_chars}")
        
        # 执行替换操作
        if do_replace:
            # 使用删除后的位置列表
            current_modifiable_pos = [idx for idx, gid in enumerate(modified_group_ids) if gid and gid != 0 and gid != 100]
            if current_modifiable_pos:
                replace_count = random.choice([1, 2]) if len(current_modifiable_pos) >= 2 else 1
                positions_to_replace = random.sample(
                    current_modifiable_pos, 
                    min(replace_count, len(current_modifiable_pos))
                )
                replace_success = True
                for pos in positions_to_replace:
                    if pos >= len(modified):
                        replace_success = False
                        break
                    char = modified[pos]
                    gid = modified_group_ids[pos]
                    new_char, log = modify_single_position(conn, char, gid)
                    
                    if not new_char:
                        if DEBUG_MODE:
                            print(f"【调试】{original_hira}：替换失败（{log}）")
                        replace_success = False
                        break
                    modified[pos] = new_char
                    operation_performed = True
                
                # 如果替换失败，但之前有删除操作，仍然保留删除的结果
                # 如果替换失败且没有删除操作，跳过这次尝试
                if not replace_success and not operation_performed:
                    continue
        
        # 如果执行了操作，添加到错误选项集合
        if operation_performed:
            wrong_opt = "".join(modified)
            # 确保结果不为空且与原始不同
            if wrong_opt and wrong_opt != original_hira and len(wrong_opt) > 0:
                wrong_opts.add(wrong_opt)
                if DEBUG_MODE:
                    print(f"【调试】{original_hira} → {wrong_opt}")

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
    
    # 检查题目显示的单词是否与四个选项中的任何一个完全一样
    # 如果一样，则需要显示中文意思而不是日文单词，避免题目和选项重复
    show_meaning = (word in all_opts)
    meaning = None
    if show_meaning:
        # 从数据库获取单词的中文意思
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT meaning FROM vocabulary WHERE word = ? LIMIT 1;",
                (word,)
            )
            row = cursor.fetchone()
            if row and row[0]:
                meaning = row[0]
            else:
                # 如果获取不到中文意思，跳过这道题
                # 因为题目和选项会完全一样，没有测试意义
                if DEBUG_MODE:
                    print(f"【调试】单词 {word} 与平假名相同但无中文意思，跳过此题")
                return None
        except Error as e:
            if DEBUG_MODE:
                print(f"【调试】获取单词意思失败：{e}")
            # 查询失败时也跳过此题
            return None
        finally:
            if cursor:
                cursor.close()
    
    return {
        "word": word,
        "correct": original_hira,
        "options": all_opts,
        "show_meaning": show_meaning,
        "meaning": meaning
    }
# 你原有的 kana_test.py 代码（不变）
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import random


# ------------------- 基础工具函数 -------------------
def get_db_connection():
    """获取数据库连接（内部复用，无需外部调用）"""
    load_dotenv()
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            port=3306,
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"❌ 数据库连接失败：{e}")
    return None


def get_modifiable_positions(group_id_list):
    """收集可修改的字符位置（排除group_id=None/0）"""
    return [
        idx for idx, group_id in enumerate(group_id_list)
        if group_id is not None and group_id != 0
    ]


def modify_single_position(connection, chars, group_ids, target_idx):
    """修改单个位置的字符（删除/调换），返回修改后的数据和日志"""
    current_char = chars[target_idx]
    current_group_id = group_ids[target_idx]
    modify_log = ""

    # 规则1：group_id=100 → 删除字符
    if current_group_id == 100:
        deleted_char = chars.pop(target_idx)
        group_ids.pop(target_idx)
        modify_log = f"删除位置{target_idx}的「{deleted_char}」（group_id=100）"
        return chars, group_ids, modify_log

    # 规则2：其他group_id → 调换同组字符
    cursor = None
    try:
        cursor = connection.cursor()
        sql = "SELECT kana FROM japanese_kana WHERE confusion_group_id = %s AND kana != %s LIMIT 10;"
        cursor.execute(sql, (current_group_id, current_char))
        candidates = [item[0] for item in cursor.fetchall() if item[0]]
        
        if not candidates:
            return None, None, f"位置{target_idx}无替换字符（group_id={current_group_id}）"
        
        target_char = random.choice(candidates)
        chars[target_idx] = target_char
        modify_log = f"位置{target_idx}「{current_char}」→「{target_char}」（group_id={current_group_id}）"
        return chars, group_ids, modify_log
    except Error as e:
        return None, None, f"修改出错：{e}"
    finally:
        if cursor:
            cursor.close()


# ------------------- 核心版本生成函数 -------------------
def generate_single_wrong_version(connection, original_chars, original_group_ids):
    """生成1个独立的错误版本（与原始单词不同）"""
    chars = original_chars.copy()
    group_ids = original_group_ids.copy()
    original_str = ''.join(original_chars)
    modifiable_pos = get_modifiable_positions(original_group_ids)

    # 无可用修改位置，返回失败
    if not modifiable_pos:
        return {"status": "failed", "reason": "无可用修改位置"}

    # 随机选择修改1-2处（增加多样性）
    max_modify = min(2, len(modifiable_pos))
    modify_count = random.choice(range(1, max_modify + 1))
    selected_pos = random.sample(modifiable_pos, modify_count)
    selected_pos.sort(reverse=True)  # 倒序修改，避免索引偏移

    modify_logs = []
    success = True
    for idx in selected_pos:
        if idx >= len(chars):
            modify_logs.append(f"位置{idx}已失效（跳过）")
            continue
        
        updated_chars, updated_group_ids, log = modify_single_position(
            connection, chars, group_ids, idx
        )
        if updated_chars is None:
            success = False
            modify_logs.append(log)
            break
        
        chars, group_ids = updated_chars, updated_group_ids
        modify_logs.append(log)

    # 验证修改结果（必须与原始不同）
    wrong_str = ''.join(chars)
    if success and wrong_str != original_str:
        return {
            "status": "success",
            "wrong_string": wrong_str,
            "modify_logs": modify_logs
        }
    return {"status": "failed", "reason": "修改后与原始相同或失败", "logs": modify_logs}


# ------------------- 对外暴露的核心函数 -------------------
def generate_question_options(
    connection,        # 外部传入的数据库连接
    original_hiragana, # 指定的原始平假名（不再从数据库抽单词）
    wrong_option_count=3,
    max_attempts=20
):
    original_chars = list(original_hiragana)
    char_group_id_list = []
    cursor = None

    # 1. 获取原始平假名对应的confusion_group_id
    try:
        cursor = connection.cursor()
        placeholders = ', '.join(['%s'] * len(original_chars))
        sql = f"SELECT kana, confusion_group_id FROM japanese_kana WHERE kana IN ({placeholders})"
        cursor.execute(sql, tuple(original_chars))
        kana_to_group = dict(cursor.fetchall())
        char_group_id_list = [kana_to_group.get(char, None) for char in original_chars]
    except Error as e:
        return {"success": False, "reason": f"获取group_id失败：{e}"}
    finally:
        if cursor:
            cursor.close()

    # 2. 生成错误选项
    wrong_options = []
    used_wrong_strings = set()
    attempt_count = 0

    while len(wrong_options) < wrong_option_count and attempt_count < max_attempts:
        attempt_count += 1
        # 调用原生成错误版本的函数（generate_single_wrong_version）
        version = generate_single_wrong_version(connection, original_chars, char_group_id_list)
        if version["status"] == "success":
            wrong_str = version["wrong_string"]
            if wrong_str not in used_wrong_strings and wrong_str != original_hiragana:
                used_wrong_strings.add(wrong_str)
                wrong_options.append(wrong_str)

    # 3. 返回结果（含混排选项）
    if len(wrong_options) < wrong_option_count:
        return {
            "success": False,
            "reason": f"仅生成{len(wrong_options)}/{wrong_option_count}个错误选项",
            "wrong_options": wrong_options
        }
    all_options = wrong_options + [original_hiragana]
    random.shuffle(all_options)
    return {
        "success": True,
        "correct_kana": original_hiragana,
        "shuffled_options": all_options
    }


# ------------------- 新增：缺失的 2 个核心函数 -------------------
def parse_lesson_input():
    """新增：让用户选择测试范围（单个课/范围/all），返回数据库查询用的正则模式"""
    while True:
        user_input = input("请选择测试范围（输入1-48的单个课数/范围，或all表示全部）：").strip().lower()
        # 1. 全部课文
        if user_input == "all":
            print(f"✅ 已选择：全部1-48课\n")
            return r"第[1-9]\d*课"  # 匹配所有“第X课”的正则
        # 2. 单个课数（如：3 → 第3课）
        if user_input.isdigit():
            lesson_num = int(user_input)
            if 1 <= lesson_num <= 48:
                pattern = f"第{lesson_num}课"
                print(f"✅ 已选择：第{lesson_num}课\n")
                return pattern
            else:
                print("❌ 课数超出范围！请输入1-48之间的数字。")
                continue
        # 3. 课数范围（如：1-5 → 第1-5课）
        if "-" in user_input:
            parts = user_input.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                start, end = int(parts[0]), int(parts[1])
                if 1 <= start <= end <= 48:
                    pattern = "|".join([f"第{i}课" for i in range(start, end + 1)])
                    print(f"✅ 已选择：第{start}-{end}课\n")
                    return pattern
                else:
                    print("❌ 范围无效！请确保开始≤结束，且在1-48之间（如1-5）。")
                    continue
        # 4. 输入格式错误
        print("❌ 输入格式错误！请输入：\n- 单个课数（如3）\n- 课数范围（如1-5）\n- all（全部课文）")


def run_kana_only_quiz(connection, lesson_pattern, total_questions=15):
    """新增：执行纯平假名测试流程（调用generate_question_options生成选项）"""
    print("=" * 50)
    print("🎯 平假名识别测试规则")
    print(f"📝 根据显示的日文单词，选择对应的正确平假名")
    print(f"📊 共{total_questions}题，输入'exit'可随时退出")
    print("=" * 50 + "\n")
    
    correct_count = 0  # 正确题数
    completed_count = 0  # 已完成题数
    cursor = None

    for q_num in range(1, total_questions + 1):
        # 1. 从指定范围随机获取1个带平假名的单词（依赖vocabulary表）
        try:
            cursor = connection.cursor(dictionary=True)
            # 只查有平假名的单词，避免无效数据
            sql = """
                SELECT word, hiragana 
                FROM vocabulary 
                WHERE lesson REGEXP %s 
                  AND hiragana IS NOT NULL 
                  AND hiragana != '' 
                ORDER BY RAND() 
                LIMIT 1
            """
            cursor.execute(sql, (lesson_pattern,))
            word_data = cursor.fetchone()
            if not word_data:
                print(f"\n⚠️  该范围暂无带平假名的单词，测试提前结束")
                break
            target_word = word_data["word"]  # 日文单词
            correct_kana = word_data["hiragana"]  # 正确平假名
            completed_count += 1

        except Error as e:
            print(f"第{q_num}题 ⚠️  单词查询错误：{e}，跳过本题\n")
            continue
        finally:
            if cursor:
                cursor.close()

        # 2. 调用你原有的generate_question_options生成：正确+3个错误选项
        kana_result = generate_question_options(
            connection=connection,
            original_hiragana=correct_kana,  # 传入正确平假名
            wrong_option_count=3
        )

        # 3. 处理选项生成失败的情况
        if not kana_result["success"]:
            print(f"第{q_num}题 ⚠️  选项生成失败：{kana_result['reason']}，跳过本题\n")
            completed_count -= 1
            continue

        # 4. 展示题目和选项
        shuffled_options = kana_result["shuffled_options"]
        print(f"第{q_num}题：单词「{target_word}」的正确平假名是？")
        for idx, option in enumerate(shuffled_options, 1):
            print(f"  {idx}. {option}")

        # 5. 获取用户输入（支持exit退出）
        while True:
            user_input = input("请输入选项编号（1-4）：").strip().lower()
            # 中途退出
            if user_input == "exit":
                print(f"\n📊 测试终止！已完成{completed_count}题，正确率：{correct_count}/{completed_count}" if completed_count > 0 else "📊 测试未开始")
                return
            # 验证输入有效性
            if user_input in ["1", "2", "3", "4"]:
                user_choice = shuffled_options[int(user_input) - 1]
                break
            print("❌ 无效输入！请输入1-4之间的数字。")

        # 6. 判断答案并反馈
        if user_choice == correct_kana:
            print("✅ 回答正确！\n")
            correct_count += 1
        else:
            print(f"❌ 回答错误！正确答案是：{correct_kana}\n")

    # 7. 测试结束，显示统计结果
    if completed_count == 0:
        print("\n📊 未完成任何题目")
    else:
        accuracy = (correct_count / completed_count) * 100 if completed_count > 0 else 0
        print(f"🎉 测试结束！共完成{completed_count}题（计划{total_questions}题）")
        print(f"📊 正确率：{correct_count}/{completed_count}（{accuracy:.1f}%）")


# ------------------- 本地测试（不变） -------------------
if __name__ == "__main__":
    print("="*60)
    print("🎯 本地测试：生成题目选项")
    print("="*60 + "\n")

    # 调用核心函数生成选项（需先获取连接）
    conn = get_db_connection()
    if conn:
        # 示例：用一个测试平假名调用（如“さようなら”）
        test_kana = "さようなら"
        question_data = generate_question_options(
            connection=conn,
            original_hiragana=test_kana,
            wrong_option_count=3
        )

        if question_data["success"]:
            print(f"✅ 生成成功！")
            print(f"正确平假名：{question_data['correct_kana']}")
            print(f"混排选项：{question_data['shuffled_options']}\n")
        else:
            print(f"❌ 生成失败：{question_data['reason']}")
        conn.close()
    else:
        print("❌ 无法连接数据库，本地测试失败")
    print("="*60)
    print("🎯 本地测试：生成题目选项")
    print("="*60 + "\n")

    # 调用核心函数生成选项
    question_data = generate_question_options(wrong_option_count=3)

    if question_data["success"]:
        print(f"✅ 生成成功！")
        print(f"正确选项：{question_data['correct_option']}")
        print(f"错误选项：{question_data['wrong_options']}")
        print(f"混排选项（用户选择用）：{question_data['all_options']}\n")
        
        # 打印详细日志（调试用）
        print("📝 错误选项生成详情：")
        for idx, detail in enumerate(question_data["detail"], 1):
            print(f"  错误选项{idx}（{detail['wrong_string']}）：{detail['modify_logs']}")
    else:
        print(f"❌ 生成失败：{question_data['reason']}")
        if "correct_option" in question_data:
            print(f"已获取的正确选项：{question_data['correct_option']}")
        if "wrong_options" in question_data and question_data["wrong_options"]:
            print(f"已生成的错误选项：{question_data['wrong_options']}")


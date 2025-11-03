import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import random
# 导入kana_test的核心函数（确保两文件在同一目录）
from kana_test import generate_question_options


# ------------------- 工具函数：输入解析与范围处理 -------------------
def parse_lesson_input():
    """解析用户输入的测试范围（单个课/范围/all），返回范围类型和正则模式"""
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


def fetch_random_word_with_kana(connection, lesson_pattern):
    """从指定范围随机获取1个带平假名的单词（返回：单词、正确平假名；无数据则返回None）"""
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        # 只查询有平假名的单词（避免无数据可用）
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
        result = cursor.fetchone()
        if not result:
            return None  # 无符合条件的单词
        return result["word"], result["hiragana"]  # （日文单词，正确平假名）
    except Error as e:
        print(f"❌ 单词查询错误：{e}")
        return None
    finally:
        if cursor:
            cursor.close()


# ------------------- 核心测试函数：仅平假名识别 -------------------
def run_kana_only_quiz(connection, lesson_pattern, total_questions=15):
    """执行纯平假名识别测试：显示单词→选择正确平假名"""
    print("=" * 50)
    print("🎯 平假名识别测试（仅1种题型）")
    print(f"📝 规则：根据显示的日文单词，选择对应的正确平假名")
    print(f"📊 共{total_questions}题，输入'exit'可随时退出")
    print("=" * 50 + "\n")
    
    correct_count = 0  # 正确题数
    completed_count = 0  # 已完成题数

    for q_num in range(1, total_questions + 1):
        # 1. 获取带平假名的随机单词（无数据则终止）
        word_data = fetch_random_word_with_kana(connection, lesson_pattern)
        if not word_data:
            print(f"\n⚠️  该范围暂无带平假名的单词，测试提前结束")
            break
        target_word, correct_kana = word_data  # 目标单词 + 正确平假名
        completed_count += 1

        # 2. 调用kana_test生成：正确平假名 + 3个错误平假名（混排选项）
        kana_options_result = generate_question_options(
            connection=connection,        # 复用数据库连接
            original_hiragana=correct_kana,  # 基于正确平假名生成错误选项
            wrong_option_count=3          # 固定3个错误选项
        )

        # 3. 处理选项生成失败的情况（跳过本题）
        if not kana_options_result["success"]:
            print(f"第{q_num}题 ⚠️  选项生成失败：{kana_options_result['reason']}，跳过本题\n")
            completed_count -= 1  # 跳过不计入已完成
            continue

        # 4. 提取混排后的选项（正确+错误）
        shuffled_options = kana_options_result["shuffled_options"]

        # 5. 展示题目与选项
        print(f"第{q_num}题：日文单词「{target_word}」对应的正确平假名是？")
        for idx, option in enumerate(shuffled_options, 1):
            print(f"  {idx}. {option}")

        # 6. 获取用户输入（支持exit退出，验证输入有效性）
        while True:
            user_input = input("请输入选项编号（1-4）：").strip().lower()
            # 中途退出测试
            if user_input == "exit":
                print(f"\n📊 测试主动终止！已完成{completed_count}题，正确率：{correct_count}/{completed_count}" if completed_count > 0 else "📊 测试未开始")
                return
            # 验证输入是1-4的数字
            if user_input in ["1", "2", "3", "4"]:
                user_choice = shuffled_options[int(user_input) - 1]
                break
            print("❌ 无效输入！请输入1-4之间的数字。")

        # 7. 判断答案并反馈
        if user_choice == correct_kana:
            print("✅ 回答正确！\n")
            correct_count += 1
        else:
            print(f"❌ 回答错误！正确答案是：{correct_kana}\n")

    # 8. 测试完成（答完所有题或无数据）
    if completed_count == 0:
        print("\n📊 未完成任何题目")
    else:
        accuracy = (correct_count / completed_count) * 100 if completed_count > 0 else 0
        print(f"🎉 测试结束！共完成{completed_count}题（计划{total_questions}题）")
        print(f"📊 正确率：{correct_count}/{completed_count}（{accuracy:.1f}%）")


# ------------------- 数据库连接与入口函数 -------------------
def get_db_connection():
    """获取数据库连接（简化日志，仅关键提示）"""
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
            print("✅ 数据库连接成功\n")
            return connection
    except Error as e:
        print(f"❌ 数据库连接失败：{e}（请检查.env配置）")
    return None


def main():
    # 1. 建立数据库连接（连接失败则退出）
    db_connection = get_db_connection()
    if not db_connection:
        return

    try:
        # 2. 显示欢迎信息 + 解析测试范围
        print("=" * 60)
        print("🎯 日文单词平假名识别测试系统（纯平假名模式）")
        print("=" * 60)
        lesson_regex_pattern = parse_lesson_input()

        # 3. 执行纯平假名测试（可修改total_questions调整题数）
        run_kana_only_quiz(
            connection=db_connection,
            lesson_pattern=lesson_regex_pattern,
            total_questions=15  # 默认15题，可按需修改
        )

    finally:
        # 4. 确保数据库连接关闭（无论测试是否正常结束）
        if db_connection.is_connected():
            db_connection.close()
            print("\n🔚 数据库连接已关闭")


if __name__ == "__main__":
    main()
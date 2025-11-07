import sys
import os
# 把 test.py 所在目录（src/core）加入 Python 模块搜索路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import random
# 导入工具模块的核心类和函数
from random_kana import SQLiteDB, generate_question, DEBUG_MODE
from user_note import ensure_user_note_table, record_wrong_word

# ------------------- 全局配置（应用逻辑专属：题目数量选项）-------------------
QUESTION_COUNT_OPTIONS = [10, 20, 30, 40, 50]  # 用户可选择的题目数量


# ------------------- 用户交互函数（应用逻辑专属）-------------------
def parse_question_count():
    """让用户选择题目数量（仅支持固定选项）"""
    print("\n请选择测试题目数量（仅支持以下选项）：")
    for i, count in enumerate(QUESTION_COUNT_OPTIONS, 1):
        print(f"  {i}. {count}道题")
    
    while True:
        user_input = input("请输入选项编号（1-5）：").strip()
        if not user_input.isdigit():
            print("❌ 请输入数字编号！")
            continue
        
        idx = int(user_input) - 1
        if 0 <= idx < len(QUESTION_COUNT_OPTIONS):
            selected = QUESTION_COUNT_OPTIONS[idx]
            print(f"✅ 已选择：{selected}道题")
            return selected
        else:
            print(f"❌ 请输入1-{len(QUESTION_COUNT_OPTIONS)}之间的编号！")


def parse_lesson_input():
    """选择课程范围（应用逻辑专属）"""
    print("\n请选择测试课程范围：")
    print("  - 输入 'all' → 全部48课")
    print("  - 输入数字（如1）→ 单课")
    print("  - 输入范围（如1-7）→ 多课")
    
    while True:
        inp = input("请输入：").strip().lower()
        if not inp:
            print("❌ 输入不能为空！")
            continue

        # 处理all
        if inp == "all":
            print("✅ 已选择：全部48课")
            return "all"

        # 处理单课
        if inp.isdigit():
            num = int(inp)
            if 1 <= num <= 48:
                lesson = f"第{num}课"
                print(f"✅ 已选择：{lesson}")
                return lesson
            print("❌ 课数需在1-48之间！")
            continue

        # 处理范围
        if "-" in inp:
            parts = inp.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                start, end = int(parts[0]), int(parts[1])
                if 1 <= start <= end <= 48:
                    lessons = [f"第{i}课" for i in range(start, end + 1)]
                    print(f"✅ 已选择：第{start}-{end}课（共{len(lessons)}课）")
                    return lessons
                print("❌ 范围需满足1≤开始≤结束≤48！")
            else:
                print("❌ 范围格式错误（示例：1-7）！")
            continue

        print("❌ 支持格式：all/单数字/范围（如1-7）！")


# ------------------- 主测试流程（应用逻辑核心）-------------------
def run_kana_test():
    """
    对外提供的核心调用接口：启动平假名测试
    用户只需在主程序中调用 test.run_kana_test() 即可
    """
    print("="*60)
    print("🎯 平假名识别测试系统（SQLite版）")
    print("="*60)

    # 初始化数据库连接（使用上下文管理器自动管理）
    db = SQLiteDB()
    try:
        with db as conn:
            ensure_user_note_table(conn)
            # 1. 步骤1：用户选择课程范围
            lesson_pattern = parse_lesson_input()
            # 2. 步骤2：用户选择题目数量
            target_question_count = parse_question_count()
            # 3. 步骤3：查询所有带平假名的单词
            all_valid_words = SQLiteDB.query_valid_words(conn, lesson_pattern)
            
            if len(all_valid_words) == 0:
                print("⚠️  无带平假名的单词，测试终止！")
                return

            # 4. 步骤4：筛选有效题（跳过无法生成足够错误选项的单词）
            print(f"\n【筛选有效题】需筛选{target_question_count}道有效题（跳过无效题）...")
            valid_questions = []
            random.shuffle(all_valid_words)  # 随机遍历，避免固定顺序

            for word, hira in all_valid_words:
                if len(valid_questions) >= target_question_count:
                    break  # 已凑够题目，停止筛选
                
                # 调用工具模块的函数生成题目
                question = generate_question(conn, word, hira)
                if question:
                    valid_questions.append(question)
                    # 打印筛选进度（每5道更一次）
                    if len(valid_questions) % 5 == 0 or len(valid_questions) == target_question_count:
                        print(f"  → 已筛选{len(valid_questions)}/{target_question_count}道有效题")

            # 5. 步骤5：处理有效题不足的情况
            actual_count = len(valid_questions)
            if actual_count == 0:
                print("⚠️  无有效题可测（所有单词均无法生成足够错误选项），测试终止！")
                return
            if actual_count < target_question_count:
                print(f"⚠️  有效题不足{target_question_count}道，实际可测{actual_count}道（已尽力筛选）")

            # 6. 步骤6：执行测试
            correct_count = 0
            print(f"\n" + "="*60)
            print(f"🎯 平假名测试开始（共{actual_count}道题，输入'exit'中途退出）")
            print(f"="*60)

            for idx, q in enumerate(valid_questions, 1):
                print(f"\n【第{idx}/{actual_count}题】")
                print(f"单词：{q['word']}")
                print("请选择正确平假名：")
                for opt_idx, opt in enumerate(q["options"], 1):
                    print(f"  {opt_idx}. {opt}")

                # 处理用户输入
                while True:
                    inp = input("你的选择（1-4/exit）：").strip().lower()
                    if inp == "exit":
                        print(f"\n🛑 测试中途退出")
                        completed = idx - 1
                        if completed > 0:
                            acc = (correct_count / completed) * 100
                            print(f"📊 已完成{completed}题，正确率：{correct_count}/{completed}（{acc:.1f}%）")
                        return
                    if inp.isdigit() and 1 <= int(inp) <= len(q["options"]):
                        user_choice = q["options"][int(inp) - 1]
                        break
                    print(f"❌ 请输入1-{len(q['options'])}或'exit'！")

                # 判分
                if user_choice == q["correct"]:
                    print("✅ 回答正确！")
                    correct_count += 1
                else:
                    print(f"❌ 回答错误！正确答案：{q['correct']}")
                    record_wrong_word(conn, q['word'])

            # 7. 步骤7：展示最终成绩
            acc = (correct_count / actual_count) * 100
            print(f"\n" + "="*60)
            print(f"🎉 测试完成（共{actual_count}道题）")
            print(f"📊 成绩：正确{correct_count}道 / 总{actual_count}道")
            print(f"📊 正确率：{acc:.1f}%")
            print("="*60)

    except Exception as e:
        print(f"\n❌ 程序异常退出：{e}")
    finally:
        print(f"\n👋 程序已结束")


# ------------------- 测试入口（本地运行test.py时触发）-------------------
if __name__ == "__main__":
    run_kana_test()
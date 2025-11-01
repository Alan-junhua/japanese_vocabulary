import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import random
import re

# 随机测试功能
def test(connection):
    while True:
        try:
            print("随机测试模式：")
            print("请选择你要测试的课文范围（1—48）：")
            lesson_range = input("输入课文范围（例如1-5，或all表示全部课文）：").strip()

            if lesson_range.lower() == "all":
                all_tests(connection)
            else:
                try:
                    start, end = map(int, lesson_range.split('-'))
                    if start < 1 or end > 48 or start > end:
                        print("无效的课文范围，请输入1到48之间的范围，例如1-5。")
                        continue
                    range_tests(connection, start, end)
                except ValueError:
                    print("输入格式错误，请输入正确的课文范围，例如1-5，或all表示全部课文。")
                    continue
        except Exception as e:
            print(f"发生错误：{e}")
            continue  # 重新开始循环

#整本书随机测试
def all_tests(connection):
    print("\n" + "=" * 50)
    print("开始全部课文的随机测试（共15题，输入'exit'可随时退出）")
    print("规则：随机出题，可能需要翻译日文单词，也可能需要翻译中文意思")
    print("=" * 50)

    cursor = None
    try:
        cursor = connection.cursor()
        counter = 0

        while counter < 15:
            # 获取随机单词
            cursor.execute("SELECT word, meaning FROM vocabulary ORDER BY RAND() LIMIT 1")
            result = cursor.fetchone()

            if not result:
                print("未找到单词，测试结束。")
                break  # 退出测试循环

            target_word, target_meaning = result
            
            # 随机选择测试类型
            test_type = random.choice(["word_to_meaning", "meaning_to_word"])

            # 看单词选中文意思
            if test_type == "word_to_meaning":
                # 随机生成三个干扰选项
                cursor.execute("SELECT meaning FROM vocabulary WHERE meaning != %s ORDER BY RAND() LIMIT 3", (target_meaning,))
                distractors = [row[0] for row in cursor.fetchall()]
                # 确保有足够的干扰项
                if len(distractors) < 3:
                    print("警告：干扰项不足，可能影响测试效果")
                    while len(distractors) < 3:
                        distractors.append("(无选项)")
                
                options = [target_meaning] + distractors
                random.shuffle(options)   # 打乱选项顺序

                # 显示题目与选项
                print(f"\n第{counter + 1}题; 单词：{target_word}的正确中文意思是？")
                for idx, option in enumerate(options, 1):
                    print(f"{idx}. {option}")
                    
                while True:
                    user_input = input("请输入你的选择（1-4）:").strip()
                    if user_input.lower() == 'exit':
                        print("测试结束")
                        return
                    if user_input not in ['1', '2', '3', '4']:
                        print("无效的选择，请输入1—4之间的数字。")
                        continue
                    break

                # 判断答案是否正确
                selected_meaning = options[int(user_input) - 1]
                if selected_meaning == target_meaning:
                    print("回答正确！")
                else:
                    print(f"回答错误！正确的答案是{target_meaning}")
                counter += 1
            
            # 看中文选单词
            elif test_type == "meaning_to_word":
                # 随机生成三个干扰选项
                cursor.execute("SELECT word FROM vocabulary WHERE word != %s ORDER BY RAND() LIMIT 3", (target_word,))
                distractors = [row[0] for row in cursor.fetchall()]
                # 确保有足够的干扰项
                if len(distractors) < 3:
                    print("警告：干扰项不足，可能影响测试效果")
                    while len(distractors) < 3:
                        distractors.append("(无选项)")
                
                options = [target_word] + distractors
                random.shuffle(options)

                # 显示题目与选项
                print(f"\n第{counter + 1}题; 中文意思：{target_meaning}对应的正确单词是？")
                for idx, option in enumerate(options, 1):
                    print(f"{idx}. {option}")
         
                while True:
                    user_input = input("请输入你的选择（1-4）:").strip()
                    if user_input.lower() == 'exit':
                        print("测试结束")
                        return
                    if user_input not in ['1', '2', '3', '4']:
                        print("无效的选择，请输入1—4之间的数字。")
                        continue
                    break

                # 判断答案是否正确
                selected_word = options[int(user_input) - 1]
                if selected_word == target_word:
                    print("回答正确！")
                else:
                    print(f"回答错误！正确的答案是{target_word}")
                counter += 1
 
    except Error as e:
        print(f"数据库查询错误：{e}")
    finally:
        if cursor:
            cursor.close()

# 指定范围随机测试
def range_tests(connection, start, end):
    print("\n" + "=" * 50)
    print(f"开始第{start}到{end}课的随机测试（共15题，输入'exit'可随时退出）")
    print("规则：随机出题，可能需要翻译日文单词，也可能需要翻译中文意思")
    print("=" * 50)

    cursor = None
    try:
        cursor = connection.cursor()
        counter = 0

        # 生成课程范围匹配的模式，例如1-3会生成"第1课|第2课|第3课"
        lesson_pattern = "|".join([f"第{i}课" for i in range(start, end + 1)])
        
        while counter < 15:
            # 从指定课程范围查询单词（使用正则匹配）
            cursor.execute(
                "SELECT word, meaning FROM vocabulary WHERE lesson REGEXP %s ORDER BY RAND() LIMIT 1",
                (lesson_pattern,)
            )
            result = cursor.fetchone()

            if not result:
                print("该范围内未找到单词，测试结束。")
                break  # 退出测试循环

            target_word, target_meaning = result
            
            # 随机选择测试类型
            test_type = random.choice(["word_to_meaning", "meaning_to_word"])

            # 看单词选中文意思
            if test_type == "word_to_meaning":
                # 从指定范围生成干扰选项
                cursor.execute(
                    "SELECT meaning FROM vocabulary WHERE lesson REGEXP %s AND meaning != %s ORDER BY RAND() LIMIT 3",
                    (lesson_pattern, target_meaning)
                )
                distractors = [row[0] for row in cursor.fetchall()]
                if len(distractors) < 3:
                    print("警告：干扰项不足，可能影响测试效果")
                    while len(distractors) < 3:
                        distractors.append("(无选项)")
                
                options = [target_meaning] + distractors
                random.shuffle(options)

                print(f"\n第{counter + 1}题; 单词：{target_word}的正确中文意思是？")
                for idx, option in enumerate(options, 1):
                    print(f"{idx}. {option}")
                    
                while True:
                    user_input = input("请输入你的选择（1-4）:").strip()
                    if user_input.lower() == 'exit':
                        print("测试结束")
                        return
                    if user_input not in ['1', '2', '3', '4']:
                        print("无效的选择，请输入1—4之间的数字。")
                        continue
                    break

                selected_meaning = options[int(user_input) - 1]
                if selected_meaning == target_meaning:
                    print("回答正确！")
                else:
                    print(f"回答错误！正确的答案是{target_meaning}")
                counter += 1
            
            # 看中文选单词
            elif test_type == "meaning_to_word":
                # 从指定范围生成干扰选项
                cursor.execute(
                    "SELECT word FROM vocabulary WHERE lesson REGEXP %s AND word != %s ORDER BY RAND() LIMIT 3",
                    (lesson_pattern, target_word)
                )
                distractors = [row[0] for row in cursor.fetchall()]
                if len(distractors) < 3:
                    print("警告：干扰项不足，可能影响测试效果")
                    while len(distractors) < 3:
                        distractors.append("(无选项)")
                
                options = [target_word] + distractors
                random.shuffle(options)

                print(f"\n第{counter + 1}题; 中文意思：{target_meaning}对应的正确单词是？")
                for idx, option in enumerate(options, 1):
                    print(f"{idx}. {option}")
         
                while True:
                    user_input = input("请输入你的选择（1-4）:").strip()
                    if user_input.lower() == 'exit':
                        print("测试结束")
                        return
                    if user_input not in ['1', '2', '3', '4']:
                        print("无效的选择，请输入1—4之间的数字。")
                        continue
                    break

                selected_word = options[int(user_input) - 1]
                if selected_word == target_word:
                    print("回答正确！")
                else:
                    print(f"回答错误！正确的答案是{target_word}")
                counter += 1

    except Error as e:
        print(f"数据库查询错误：{e}")
    finally:
        if cursor:
            cursor.close()


def get_db_connection():
    load_dotenv()  # 加载环境变量
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',          # 必须使用IP，不能用localhost
            port=3306,                 # 明确指定端口
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME")
        )
        if connection.is_connected():
            print("成功连接到数据库")
            return connection
    except Error as e:
        print(f"数据库连接错误：{e}")
    return None

def main():
    connection = get_db_connection()
    if connection:
        try:
            test(connection)
        finally:
            # 确保数据库连接关闭
            if connection.is_connected():
                connection.close()
                print("数据库连接已关闭")

if __name__ == "__main__":
    main()
    main()
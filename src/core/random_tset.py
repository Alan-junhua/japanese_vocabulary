import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
import random

def test(connection):
    while True:
        try:
            print("选择你要选择哪种测试方式：")
            choice = input("1.随机测试 2.章节测试：").strip()  # 去除输入前后空格

            if choice not in ["1", "2"]:
                print("无效的选择，请输入1或2。")
                continue     # 重新开始循环

            # 随机测试
            if choice == "1":
                random_test(connection)
                continue

            # 章节测试

            elif choice == "2":
                print("章节测试功能尚未实现，敬请期待！")
            break  # 退出循环

        except Exception as e:
            print(f"发生错误：{e}")
            continue  # 重新开始循环



#随机测试函数实现
def random_test(connection):
    print("接下来，进行随机测试，根据所给出的单词，选择正确的中文意思。")
    cursor = connection.cursor()

    count = 0
    while count < 5:
        try:
            # 获取一个随机单词及其正确意思
            cursor.execute("SELECT word, meaning FROM vocabulary ORDER BY RAND() LIMIT 1")
            target_result = cursor.fetchone()

            target_word,correct_meaning = target_result
            
            # 获取三个错误选项
            cursor.execute("SELECT meaning FROM vocabulary WHERE meaning != %s ORDER BY RAND() LIMIT 3", (correct_meaning,))
            
            distractors = [row[0] for row in cursor.fetchall()]
            options = [correct_meaning] + distractors        #正确答案+3干扰项

            random.shuffle(options)  #打乱选项顺序
             
            #显示题目与选项，供用户选择
            print(f"\n第{count+1}题；单词：{target_word} 的正确中文意思是？")
            for idx, option in enumerate(options, 1):
                print(f"{idx}. {option}")

            while True:
                user_input = input("请输入你的选择（1-4）：").strip()
                if user_input not in ['1', '2', '3', '4']:
                    print("无效的选择，请输入1到4之间的数字。")
                    continue
                break

            #判断答案是否正确
            selected_meaning = options[int(user_input) - 1]
            if selected_meaning == correct_meaning:
                print("回答正确！")
            else:
                print(f"回答错误！正确答案是：{correct_meaning}")
            count += 1

        except Error as e:
            print(f"数据库查询错误：{e}")
            if 'cursor' in locals():  # 确保游标关闭
                cursor.close()
            break
    
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
        test(connection)
        connection.close()
        print("数据库连接已关闭")

if __name__ == "__main__":
    main()



import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv


def find_word(connection):  # 查找单词
    while True:
        try:
            print("请选择你要查询的方式：")
            choice = input("1.查询日文单词 2.查询中文单词：").strip()  # 去除输入前后空格

            if choice not in ["1", "2"]:
                print("无效的选择，请输入1或2。")
                continue     # 重新开始循环

            # 日语查询
            if choice == "1":
                word = input("请输入你要查询的日文单词：").strip()
                if not word:  # 检查输入是否为空
                    print("输入不能为空，请重新输入。")
                    return

                # 数据库操作
                try:
                    cursor = connection.cursor()
                    cursor.execute("SELECT word, hiragana, meaning, lesson FROM vocabulary WHERE word LIKE %s", (f'%{word}%',))
                    results = cursor.fetchall()

                    print("查询结果：")
                    if results:
                        for row in results:
                            print(f"单词：{row[0]}, 读音：{row[1]}, 中文意思：{row[2]}, 所属课文：{row[3]}")
                            print("-" * 40)
                    else:
                        print("未找到相关结果。")
                    cursor.close()

                except Error as e:
                    print(f"数据库查询错误：{e}")
                    if 'cursor' in locals():  # 确保游标关闭
                        cursor.close()
                
                
            # 中文查询
            elif choice == "2":
                meaning = input("请输入你要查询的中文单词：").strip()
                if not meaning:  # 检查输入是否为空
                    print("输入不能为空，请重新输入。")
                    return

                # 数据库操作
                try:
                    cursor = connection.cursor()
                    cursor.execute("SELECT word, hiragana, meaning, lesson lesson FROM vocabulary WHERE meaning LIKE %s", (f'%{meaning}%',))
                    results = cursor.fetchall()

                    print("查询结果：")
                    if results:
                        for row in results:
                            print(f"单词：{row[0]}, 读音：{row[1]}, 中文意思：{row[2]}, 所属课文：{row[3]}")
                            print("-" * 40)
                    else:
                        print("未找到相关结果。")
                    cursor.close()

                except Error as e:
                    print(f"数据库查询错误：{e}")
                    if 'cursor' in locals():  # 确保游标关闭
                        cursor.close()

        except Exception as e:  # 捕获其他未预料的异常
            print(f"发生错误：{e}")

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
        find_word(connection)
        connection.close()
        print("数据库连接已关闭")

if __name__ == "__main__":
    main()

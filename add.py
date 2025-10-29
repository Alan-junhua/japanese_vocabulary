import mysql.connector
from mysql.connector import Error


def add_word(connection):  #添加新的单词
    print("开始添加新单词...")

    try:
        #获得用户的输入
        word = input("请输入要添加的单词：").strip()
        hiragana = input("请输入单词的假名：").strip()
        meaning = input("请输入单词的意思：").strip()
        lesson = input("请输入单词的课文：").strip()

        #检验用户输入是否为空
        if not all([word, hiragana, meaning, lesson]):
            print("所有字段都是必填的，请重新输入。")
            return False
        
        #连接到数据库并插入新单词
        cursor = connection.cursor()    #创建数据库游标，可执行SQL语句,获得和遍历查询结果，逐行处理数据
        cursor.execute("INSERT INTO vocabulary (word, hiragana, meaning, lesson) VALUES (%s, %s, %s, %s)", (word, hiragana, meaning, lesson))
        connection.commit()

        print(f"单词添加成功：{word}({hiragana} - {meaning})")
        cursor.close()
        return True

    except Error as e:
        print(f"添加单词时出错：{e}")
        return False


#测试
if __name__ == "__main__":
    from connection import connect_to_database

    connection = connect_to_database()
    if not connection:
        print("数据库连接失败，请检查配置。")
        exit(1)

    try:
        while True:
            add_word(connection)
            cont = input("是否继续添加单词？(y/n)：").strip().lower()
            if cont != 'y':
                break

    except Exception as e:
        print(f"发生错误：{e}")

    finally:
        if connection:
            connection.close()
            print("数据库连接已关闭。")


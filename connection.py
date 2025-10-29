import mysql.connector
from mysql.connector import Error

def connect_to_database():
    """连接到MySQL数据库"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root', 
            password='zjh.060913',
            database='japanese_vocabulary'
        )
        
        if connection.is_connected():
            print("成功连接到MySQL数据库！")
            return connection
            
    except Error as e:
        print(f"连接错误: {e}")
        return None

def display_all_words(connection):
    """显示所有单词"""
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM vocabulary")
        results = cursor.fetchall()
        
        print("\n=== 所有单词 ===")
        for row in results:
            print(f"ID: {row[0]} | 单词: {row[1]} | 平假名: {row[2]} | 意思: {row[3]} | 单元: {row[4]}")
        
        cursor.close()
    except Error as e:
        print(f"查询错误: {e}")

def search_by_lesson(connection, lesson_number):
    """按单元查询单词"""
    try:
        cursor = connection.cursor()
        query = "SELECT word, hiragana, meaning FROM vocabulary WHERE lesson = %s"
        cursor.execute(query, (lesson_number,))
        results = cursor.fetchall()
        
        print(f"\n=== 第{lesson_number}单元单词 ===")
        for word, hiragana, meaning in results:
            print(f"单词: {word} ({hiragana}) - {meaning}")
        
        cursor.close()
    except Error as e:
        print(f"查询错误: {e}")
"""
def main():



   
    connection = connect_to_database()
    if connection:
        # 测试功能
        display_all_words(connection)
        
        # 查询特定单元
        lesson = input("\n第一单元第一课 ")
        search_by_lesson(connection, lesson)
        
        # 关闭连接
        connection.close()
        print("\n数据库连接已关闭")

if __name__ == "__main__":
    main()"""
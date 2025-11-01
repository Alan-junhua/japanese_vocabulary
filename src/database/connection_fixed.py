import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def connect_to_database():
    """修复命名管道错误的连接函数"""
    try:
        # 明确使用TCP/IP连接，避免命名管道
        connection = mysql.connector.connect(
            host='127.0.0.1',          
            port=3306,                 # 明确指定端口
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            use_pure=True,             # 使用纯Python实现
            auth_plugin='mysql_native_password'  # 明确指定认证插件
        )
        
        if connection.is_connected():
            print("✅ 成功连接到MySQL数据库！")
            # 测试查询
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"测试查询结果: {result}")
            cursor.close()
            return connection
            
    except mysql.connector.Error as e:
        print(f"连接错误: {e}")
        return None

# 测试连接
if __name__ == "__main__":
    conn = connect_to_database()
    if conn:
        conn.close()
        print("连接测试完成")
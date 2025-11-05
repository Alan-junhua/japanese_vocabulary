# 导入部分（确保包含 get_db_connection）
from src.core import test
from src.core import find_word
from src.core.find_word import get_db_connection  


def main():
    """日语学习主程序：整合平假名测试和词汇查找功能"""
    print("="*60)
    print("🎯 日语学习系统（功能入口）")
    print("="*60)
    
    while True:
        print("\n请选择操作：")
        print("1. 平假名识别随机测试")
        print("2. 词汇查找")
        print("3. 退出程序")
        choice = input("输入选项（1-3）：").strip()

        if choice == '1':
            test.run_kana_test()  # 调用平假名测试功能
        elif choice == '2':
            # 新增：获取连接 + 传入连接调用
            conn = get_db_connection()
            if conn:
                find_word.find_word(conn)  # 关键：传入 connection 参数
                conn.close()  # 关闭连接（重要）
            else:
                print("❌ 数据库连接失败，无法查找词汇！")
        elif choice == '3':
            print("感谢使用，程序已退出。")
            break
        else:
            print("❌ 无效选项，请重新输入！")

if __name__ == "__main__":
    main()
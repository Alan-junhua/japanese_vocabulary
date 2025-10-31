from src.database.connection_fixed import connect_to_database
from src.core.add import add_word
from src.core.find_word import find_word
from src.core.random_tset import test


def main():
    """日语词典主函数"""
    
    print("===================================")
    print("欢迎使用日语单词查询程序！")
    print("正在连接到数据库...")
    connection = connect_to_database()

    if not connection:
        print("无法连接到数据库，程序退出。")
        return
    
    while True:
        print("成功连接到日语词典数据库！")
        print("\n请选择你要进行的操作：")
        print("1. 增加单词。")
        print("2. 查找单词。")
        print("3. 随机测试。")
        
        
        choice = input("输入选项（1-5): ")
        if choice == '1':
            add_word(connection)

        elif choice == '2':
            find_word(connection)

        elif choice == '3':
            test(connection)

        else:
            print("无效的选项，请重新选择。")
            continue    
        cont = input("是否继续操作？(y/n)：").strip().lower()
        if cont != 'y':
            break
    if connection:

        connection.close()
        print("数据库连接已关闭。")

if __name__ == "__main__":
    main()


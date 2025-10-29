from connection_fixed import connect_to_database
from add import add_word

def main():
    """日语词典主函数"""

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

        choice = input("输入选项（1-5): ")
        if choice == '1':
            add_word(connection)
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


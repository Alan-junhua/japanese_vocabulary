# src/main.py（最终可运行版）
from src.database.connection_fixed import connect_to_database
from src.core.add import add_word
from src.core.find_word import find_word
# 正确导入：从kana_test（src.core下）导入2个核心函数
from src.core.kana_test import run_kana_only_quiz, parse_lesson_input


def main():
    """日语词典主函数（整合纯平假名随机测试）"""
    print("===================================")
    print("欢迎使用日语单词查询程序！")
    print("正在连接到数据库...")
    # 主程序统一创建数据库连接，传给测试函数复用
    connection = connect_to_database()

    if not connection:
        print("无法连接到数据库，程序退出。")
        return
    
    while True:
        print("\n" + "="*30)
        print("成功连接到日语词典数据库！")
        print("请选择你要进行的操作：")
        print("1. 增加单词")
        print("2. 查找单词")
        print("3. 平假名识别随机测试")
        choice = input("输入选项（1-3）: ").strip()

        if choice == '1':
            # 原有：增加单词
            add_word(connection)

        elif choice == '2':
            # 原有：查找单词
            find_word(connection)

        elif choice == '3':
            # 新增：调用平假名测试（复用主程序的数据库连接）
            print("\n" + "="*40)
            print("📌 进入平假名识别随机测试")
            print("="*40)
            # 1. 让用户选测试范围（调用parse_lesson_input）
            lesson_pattern = parse_lesson_input()
            # 2. 执行测试（调用run_kana_only_quiz，默认15题）
            run_kana_only_quiz(
                connection=connection,    # 复用连接
                lesson_pattern=lesson_pattern,
                total_questions=15        # 可修改题数（如10、20）
            )

        else:
            print("无效的选项，请重新选择（仅支持1-3）。")
            continue    
        
        # 询问是否继续其他操作
        cont = input("\n是否继续其他操作？(y/n)：").strip().lower()
        if cont != 'y':
            break
    
    # 关闭数据库连接
    if connection and connection.is_connected():
        connection.close()
        print("\n数据库连接已关闭，程序退出。")


if __name__ == "__main__":
    main()
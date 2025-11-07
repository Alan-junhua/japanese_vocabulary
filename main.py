# 导入部分（确保包含 get_db_connection）
from src.core import test
from src.core import find_word
from src.core.find_word import get_db_connection  
from src.core.lesson_words import get_lessons, get_words_by_lessons


def run_lesson_view():
    """终端：按课查看单词（与网页同源的数据逻辑）。"""
    conn = get_db_connection()
    if not conn:
        print("❌ 数据库连接失败，无法查看课次！")
        return
    try:
        while True:
            lessons = get_lessons(conn)
            if not lessons:
                print("⚠️ 未找到任何课次数据！")
                return
            print("\n可选课次（输入编号或'all'查看全部，输入'b'返回主菜单）：")
            print("  0. 全部")
            for idx, label in enumerate(lessons, 1):
                print(f"  {idx}. {label}")

            sel = input("请输入：").strip().lower()
            if sel == 'b':
                return
            if sel == 'all' or sel == '0':
                lesson_arg = 'all'
            elif sel.isdigit() and 1 <= int(sel) <= len(lessons):
                lesson_arg = lessons[int(sel) - 1]
            else:
                print("❌ 输入无效，请重试！")
                continue

            rows = get_words_by_lessons(conn, lesson_arg)
            if not rows:
                print("⚠️ 该课暂无单词。")
            else:
                print("\n单词 | 读音 | 中文意思 | 课次")
                print("-" * 60)
                for w, h, m, l in rows:
                    print(f"{w} | {h or ''} | {m or ''} | {l or ''}")

            cont = input("\n是否继续查看？(y继续 / 其他返回主菜单)：").strip().lower()
            if cont != 'y':
                return
    finally:
        conn.close()


def main():
    """日语学习主程序：整合平假名测试、词汇查找、按课查看单词"""
    print("="*60)
    print("🎯 日语学习系统（功能入口）")
    print("="*60)
    
    while True:
        print("\n请选择操作：")
        print("1. 平假名识别随机测试")
        print("2. 词汇查找")
        print("3. 按课查看单词")
        print("4. 退出程序")
        choice = input("输入选项（1-4）：").strip()

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
            run_lesson_view()
        elif choice == '4':
            print("感谢使用，程序已退出。")
            break
        else:
            print("❌ 无效选项，请重新输入！")

if __name__ == "__main__":
    main()
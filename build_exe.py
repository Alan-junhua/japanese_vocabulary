#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包脚本：将日语学习系统打包成独立可执行文件
使用方法：python build_exe.py
"""

import os
import sys
import shutil
import subprocess

def check_pyinstaller():
    """检查PyInstaller是否已安装"""
    try:
        import PyInstaller
        print(f"✓ PyInstaller已安装，版本: {PyInstaller.__version__}")
        return True
    except ImportError:
        print("❌ PyInstaller未安装，正在安装...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✓ PyInstaller安装成功")
            return True
        except subprocess.CalledProcessError:
            print("❌ PyInstaller安装失败，请手动安装：pip install pyinstaller")
            return False

def clean_build_dirs():
    """清理之前的构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理目录: {dir_name}")
            shutil.rmtree(dir_name)
    
    # 清理.spec文件生成的缓存
    if os.path.exists('japanese_learning.spec'):
        print("保留.spec配置文件")

def build_exe():
    """执行打包"""
    print("\n" + "="*60)
    print("开始打包日语学习系统...")
    print("="*60 + "\n")
    
    # 检查PyInstaller
    if not check_pyinstaller():
        return False
    
    # 清理之前的构建
    print("\n清理之前的构建文件...")
    clean_build_dirs()
    
    # 执行PyInstaller打包
    print("\n开始执行PyInstaller打包...")
    try:
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "japanese_learning.spec",
            "--clean",
            "--noconfirm"
        ]
        subprocess.check_call(cmd)
        print("\n✓ 打包成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败: {e}")
        return False

def copy_database():
    """复制数据库文件到dist目录（如果存在）"""
    db_file = "japanese_learning.db"
    dist_dir = "dist"
    
    if os.path.exists(db_file) and os.path.exists(dist_dir):
        # 查找可执行文件所在目录
        exe_name = "日语学习系统.exe" if sys.platform == "win32" else "日语学习系统"
        exe_path = os.path.join(dist_dir, exe_name)
        
        # 如果可执行文件在dist根目录
        if os.path.exists(exe_path):
            target_db = os.path.join(dist_dir, db_file)
        else:
            # 如果可执行文件在子目录
            for root, dirs, files in os.walk(dist_dir):
                if exe_name in files:
                    target_db = os.path.join(root, db_file)
                    break
            else:
                target_db = os.path.join(dist_dir, db_file)
        
        if not os.path.exists(target_db):
            shutil.copy2(db_file, target_db)
            print(f"✓ 已复制数据库文件到: {target_db}")
        else:
            print(f"ℹ 数据库文件已存在: {target_db}")

def create_readme():
    """创建使用说明文件"""
    readme_content = """# 日语学习系统 - 使用说明

## 运行程序

1. 双击运行"日语学习系统.exe"
2. 程序会自动启动Web服务器
3. 浏览器会自动打开 http://127.0.0.1:5000
4. 如果浏览器未自动打开，请手动访问上述地址

## 文件说明

- 日语学习系统.exe: 主程序文件
- japanese_learning.db: 数据库文件（包含单词和学习记录）
  - 如果数据库文件不存在，程序会自动创建
  - 学习记录会保存在此数据库中

## 注意事项

1. 首次运行可能需要几秒钟启动时间
2. 关闭程序窗口即可退出程序
3. 数据库文件请妥善保管，避免丢失学习记录
4. 如需重置数据库，删除japanese_learning.db文件即可

## 端口占用

如果5000端口被占用，程序可能无法启动。可以：
1. 关闭占用5000端口的其他程序
2. 或者修改程序代码中的端口号

## 技术支持

如有问题，请检查：
1. 防火墙是否阻止了程序运行
2. 杀毒软件是否误报
3. 程序所在目录是否有写入权限
"""
    
    dist_dir = "dist"
    if os.path.exists(dist_dir):
        readme_path = os.path.join(dist_dir, "使用说明.txt")
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print(f"✓ 已创建使用说明文件: {readme_path}")

def main():
    """主函数"""
    print("="*60)
    print("日语学习系统 - 打包脚本")
    print("="*60)
    
    # 检查必要文件
    required_files = ['web_app.py', 'japanese_learning.spec']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ 缺少必要文件: {file}")
            return
    
    # 执行打包
    if build_exe():
        # 复制数据库文件
        copy_database()
        
        # 创建使用说明
        create_readme()
        
        print("\n" + "="*60)
        print("打包完成！")
        print("="*60)
        print("\n可执行文件位于: dist/日语学习系统.exe")
        print("请将以下文件一起分发：")
        print("  - 日语学习系统.exe")
        print("  - japanese_learning.db (如果存在)")
        print("  - 使用说明.txt")
        print("\n注意：数据库文件包含学习数据，请妥善保管！")
    else:
        print("\n打包失败，请检查错误信息。")

if __name__ == "__main__":
    main()


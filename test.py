# fix_env_file.py
import os

# 定义 .env 文件的内容
env_content = """DB_HOST=127.0.0.1
DB_USER=root
DB_PASSWORD=zjh.060913
DB_NAME=japanese_vocabulary"""

env_path = os.path.join(os.getcwd(), '.env')

print(f"正在创建 .env 文件: {env_path}")

# 确保完全重写文件
with open(env_path, 'w', encoding='utf-8') as f:
    f.write(env_content)

print("✅ .env 文件已创建")

# 验证文件内容
with open(env_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("=== 验证文件内容 ===")
print(repr(content))
print("=== 文件内容结束 ===")

# 测试环境变量加载
from dotenv import load_dotenv
load_dotenv()

print("\n=== 环境变量测试 ===")
for var in ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']:
    value = os.getenv(var)
    print(f"{var}: {value}")
# -*- mode: python ; coding: utf-8 -*-
# PyInstaller配置文件：日语学习系统打包配置

block_cipher = None

a = Analysis(
    ['web_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),  # 包含模板文件
        ('static', 'static'),        # 包含静态文件
        # 注意：数据库文件不包含在打包中，将在运行时从可执行文件所在目录读取
    ],
    hiddenimports=[
        'flask',
        'sqlite3',
        'src',
        'src.core',
        'src.core.random_kana',
        'src.core.lesson_words',
        'src.core.user_note',
        'src.core.study_record',
        'src.core.find_word',
        'src.core.test',
        'werkzeug',
        'jinja2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='日语学习系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 显示控制台窗口，方便查看日志
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件路径，如：icon='icon.ico'
)


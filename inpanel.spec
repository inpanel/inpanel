# -*- mode: python ; coding: utf-8 -*-

# from src import build, version
import os.path

block_cipher = None
# bundle_identifier = 'org.inpanel.daemon'
# runtime_tmpdir = '/tmp/org.inpanel.daemon'
# root_path = os.path.dirname(__file__)

datas=[
    (os.path.join('.', 'data'), 'data'),
    (os.path.join('.', 'static'), 'static'),
    (os.path.join('.', 'templates'), 'templates')
]

a = Analysis(['src/app.py'],
             pathex=['src'],
             binaries=[],
             datas=datas,
             hiddenimports=['tornado', 'libmagic', 'pexpect', 'psutil'],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
             a.scripts,
             a.binaries,
             a.zipfiles,
             a.datas,  
             [],
             name='inpanel',
             debug=False,
             bootloader_ignore_signals=False,
             strip=False,
             upx=True,
             upx_exclude=[],
             runtime_tmpdir=None,
             console=True,
             disable_windowed_traceback=False,
             target_arch=None,
             codesign_identity=None,
             entitlements_file=None )
# coll = COLLECT(exe,
#              a.binaries,
#              a.zipfiles,
#              a.datas,
#              strip=False,
#              upx=True,
#              upx_exclude=[],
#              name='InPanel')
# app = BUNDLE(coll,
#              name='InPanel.app',
#             #  icon='resources/app.icns',
#              bundle_identifier=bundle_identifier,
#              info_plist={
#                  'CFBundleName': 'InPanel',
#                  'CFBundleDisplayName': 'InPanel',
#                  'CFBundleGetInfoString': "Jackson Dou.",
#                  'CFBundleIdentifier': bundle_identifier,
#                  'CFBundleVersion': build,
#                  'CFBundleShortVersionString': version,
#                  'NSHumanReadableCopyright': "Copyright © 2022 Jackson Dou. All Rights Reserved.",
#                  'NSHighResolutionCapable': 'True'
#              })

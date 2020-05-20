# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

spec_root = os.path.abspath(SPECPATH)



a = Analysis(['run_wist.py'],
             pathex=[spec_root, 'spec_root/../'],
             binaries=[],
             datas=[('../aws_architecture', 'aws_architecture')],
             hiddenimports=['configparser'],
             hookspath=[],
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
          [],
          exclude_binaries=True,
          name='wist',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='wist')

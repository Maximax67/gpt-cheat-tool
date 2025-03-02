# -*- mode: python ; coding: utf-8 -*-
import platform
import shutil
import os

flac_converter_dir = "services/record_audio/custom_speech_recognition"
datas = [("assets/icons", "assets/icons")]

system, machine = platform.system(), platform.machine()

if system == "Windows" and machine in {"i686", "i786", "x86", "x86_64", "AMD64"}:
    datas.append(
        (os.path.join(flac_converter_dir, "flac-win32.exe"), flac_converter_dir)
    )
elif system == "Darwin" and machine in {"i686", "i786", "x86", "x86_64", "AMD64"}:
    datas.append((os.path.join(flac_converter_dir, "flac-mac"), flac_converter_dir))
elif system == "Linux":
    if machine in {"i686", "i786", "x86"}:
        datas.append(
            (os.path.join(flac_converter_dir, "flac-linux-x86"), flac_converter_dir)
        )
    elif machine in {"x86_64", "AMD64"}:
        datas.append(
            (os.path.join(flac_converter_dir, "flac-linux-x86_64"), flac_converter_dir)
        )


a = Analysis(
    ["app.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "numpy",
        "jedi",
        "tkinter",
        "IPython",
        "lxml",
        "tzdata",
        "zstandard",
        "setuptools",
        "zmq",
        "sqlite3",
        "PIL",
        "difflib",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)

if system == "Windows":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="GPT Cheat Tool.exe",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        icon="./assets/icons/icon.ico",
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
elif system == "Darwin":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="GPT Cheat Tool",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        runtime_tmpdir=None,
        console=False,
    )
elif system == "Linux":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="gpt_cheat_tool",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        icon="./assets/icons/icon.png",
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GPT Cheat Tool",
)

if system == "Darwin":
    app = BUNDLE(
        coll,
        name="GPT Cheat Tool.app",
        icon="./assets/icons/icon.icns",
        bundle_identifier=None,
    )
elif system == "Windows":
    dir = "./dist/GPT Cheat Tool/_internal"
    pyside_dir = f"{dir}/PySide6"

    shutil.rmtree(f"{pyside_dir}/translations")

    os.remove(f"{pyside_dir}/opengl32sw.dll")
    os.remove(f"{pyside_dir}/Qt6Network.dll")
    os.remove(f"{pyside_dir}/Qt6Pdf.dll")
    os.remove(f"{pyside_dir}/Qt6Qml.dll")
    os.remove(f"{pyside_dir}/Qt6Quick.dll")
    os.remove(f"{pyside_dir}/Qt6VirtualKeyboard.dll")
    os.remove(f"{pyside_dir}/Qt6QmlModels.dll")
    os.remove(f"{pyside_dir}/Qt6QmlMeta.dll")
    os.remove(f"{pyside_dir}/Qt6QmlWorkerScript.dll")

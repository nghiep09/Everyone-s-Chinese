[app]
title = Hoc Tieng Trung
package.name = hoctiengtrung
package.domain = vn.tuhoc
source.dir = .
source.include_exts = py,json,xlsx,otf,ttf,txt,png
source.exclude_dirs = tests,docs,.git,.github,.venv,__pycache__,bin
version = 0.3.0
requirements = python3,kivy==2.3.1,openpyxl==3.1.5,et_xmlfile,pyjnius
orientation = portrait
fullscreen = 0
android.permissions = INTERNET
android.api = 34
android.minapi = 24
android.ndk_api = 24
android.ndk = 28c
android.archs = arm64-v8a
android.accept_sdk_license = True
android.add_src = android_src
android.extra_manifest_xml = ./tts_queries.xml
android.debug_artifact = apk
p4a.branch = develop

[buildozer]
log_level = 2
warn_on_root = 0

import json
import os
import re
import requests
from datetime import datetime
from . import CONFIG_FILE

try:
    from charset_normalizer import from_bytes
except ImportError:
    from_bytes = None


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_session():
    config = load_config()
    session = requests.Session()
    if "cookies" in config:
        for name, value in config["cookies"].items():
            session.cookies.set(name, value)
    return session


def save_cookies(session, username=None):
    config = load_config()
    config["cookies"] = session.cookies.get_dict()
    if username:
        config["username"] = username
    save_config(config)


def validate_slug(slug):
    """验证slug是否符合服务器要求：仅支持a-z、0-9、_、-，长度3-48"""
    import re
    if len(slug) < 3 or len(slug) > 48:
        return False, f"链接长度必须在3-48个字符之间（当前：{len(slug)}）"
    if not re.match(r'^[a-z0-9_-]+$', slug):
        return False, "链接仅支持小写字母(a-z)、数字(0-9)、下划线(_)和连字符(-)"
    return True, ""


def read_file_text(filepath):
    """读取文件文本内容，自动检测编码，二进制文件给出友好提示"""
    BINARY_EXTENSIONS = {
        '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
        '.pdf', '.zip', '.rar', '.7z', '.exe', '.dll',
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico',
        '.mp3', '.mp4', '.avi', '.mkv', '.mov',
        '.pyc', '.class', '.o', '.so', '.dylib', '.lib',
        '.wps', '.et', '.dps',
    }

    ext = os.path.splitext(filepath)[1].lower()
    if ext in BINARY_EXTENSIONS:
        raise ValueError(
            f"'{filepath}' 是二进制文件（{ext}），pen 只支持推送纯文本文件，\n"
            f"请使用 .txt、.md、.py、.json、.html、.css、.js、.log 等纯文本格式"
        )

    with open(filepath, 'rb') as f:
        raw_data = f.read()

    null_ratio = raw_data.count(b'\x00') / max(len(raw_data), 1)
    if null_ratio > 0.05:
        raise ValueError(
            f"'{filepath}' 检测为二进制文件，pen 只支持推送纯文本文件"
        )

    if raw_data.startswith(b'\xef\xbb\xbf'):
        try:
            return raw_data.decode('utf-8-sig')
        except UnicodeDecodeError:
            pass

    if from_bytes is not None:
        try:
            results = from_bytes(raw_data)
            if results:
                best = results.best()
                if best.encoding:
                    return raw_data.decode(best.encoding)
        except Exception:
            pass

    for enc in ['utf-8', 'gbk', 'gb18030', 'gb2312', 'latin-1']:
        try:
            return raw_data.decode(enc)
        except (UnicodeDecodeError, UnicodeError):
            continue

    raise ValueError(f"无法识别文件编码: {filepath}")


def track_visit(slug):
    config = load_config()
    if "visited" not in config:
        config["visited"] = []
    for v in config["visited"]:
        if v["slug"] == slug:
            v["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_config(config)
            return
    config["visited"].append({
        "slug": slug,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    save_config(config)

# Pen 全面优化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 pen.py 单文件（~710 行）拆分为 pen/ 包结构，同时修复 8 个优化点：错误提示、死代码清理、异常处理、功能补全、shell 补全、REPL 增强、pytest 测试。

**Architecture:** 拆分为三层包结构 — `pen/__init__.py`（常量）、`pen/utils.py`（配置/文件/校验）、`pen/api.py`（API 封装）、`pen/cli.py`（Click 命令+REPL+入口）。保留 `pen.py` 作为薄入口。拆分后再对新文件逐一优化。

**Tech Stack:** Python 3, Click, requests, charset-normalizer, pytest

**分为两个 Phase：**
- **Phase 1 (Tasks 1-5):** 文件拆分，不改行为
- **Phase 2 (Tasks 6-13):** 八项优化

---

## Phase 1: 文件拆分

### 现有 pen.py 的内容归属

| 行号 | 内容 | 归属 |
|------|------|------|
| 1-18 | import 语句 + charset_normalizer 导入 | 按需分到各模块 |
| 20-22 | VERSION, BASE_URL, CONFIG_FILE | `pen/__init__.py` |
| 24-47 | load_config, save_config, get_session, save_cookies | `pen/utils.py` |
| 49-60 | get_paste_content | `pen/api.py` |
| 62-69 | validate_slug | `pen/utils.py` |
| 71-120 | read_file_text | `pen/utils.py` |
| 122-144 | set_paste_content | `pen/api.py` |
| 146-155 | track_visit | `pen/utils.py` |
| 157-162 | cli group | `pen/cli.py` |
| 164-201 | register | `pen/cli.py` |
| 204-232 | login | `pen/cli.py` |
| 234-259 | pull | `pen/cli.py` |
| 261-299 | push | `pen/cli.py` |
| 301-323 | add | `pen/cli.py` |
| 325-334 | del | `pen/cli.py` |
| 336-380 | log | `pen/cli.py` |
| 382-427 | open | `pen/cli.py` |
| 429-445 | logout | `pen/cli.py` |
| 447-497 | status | `pen/cli.py` |
| 499-505 | surf | `pen/cli.py` |
| 507-551 | clip | `pen/cli.py` |
| 553-596 | init | `pen/cli.py` |
| 598-647 | help | `pen/cli.py` |
| 649-710 | run_interactive + main | `pen/cli.py` |

---

### Task 1: 创建 pen/__init__.py

**Files:**
- Create: `pen/__init__.py`

```python
VERSION = "1.9.0"
BASE_URL = "https://paste.moxiao.site"
```

---

### Task 2: 创建 pen/utils.py

**Files:**
- Create: `pen/utils.py`

从 pen.py 提取以下函数（保持原样，仅修改 import 路径）：

- `load_config()` — 使用 `pen.__init__` 中的 `BASE_URL` 和从 `pen/__init__.py` 导出的 `CONFIG_FILE`
- `save_config(config)`
- `get_session()`
- `save_cookies(session, username=None)`
- `validate_slug(slug)`
- `read_file_text(filepath)`
- `track_visit(slug)`

需要移到 utils 的 import：
```python
import json
import os
import re
import requests
from . import CONFIG_FILE  # will be defined in __init__.py
```

**注意：** CONFIG_FILE 依赖 `os.path.expanduser`，改在 `__init__.py` 中定义：
```python
import os
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".pen_config.json")
```

---

### Task 3: 创建 pen/api.py

**Files:**
- Create: `pen/api.py`

从 pen.py 提取：
- `get_paste_content(slug, session=None)`
- `set_paste_content(slug, content, session=None, visibility="public_read", expires_at=None)`

需要的 import：
```python
import requests
from . import BASE_URL
from .utils import get_session, validate_slug
```

---

### Task 4: 创建 pen/cli.py

**Files:**
- Create: `pen/cli.py`

包含所有 Click 命令 + `run_interactive()` + 入口函数 `main()`。

需要的 import（按需整合，去掉不再直接使用的模块）：
```python
import click
import requests
import os
import sys
import tempfile
import subprocess
import platform
import shlex
import webbrowser
import time
from datetime import datetime

from . import VERSION, BASE_URL
from .utils import (
    load_config, save_config, get_session, save_cookies,
    read_file_text, validate_slug, track_visit,
)
from .api import get_paste_content, set_paste_content
```

入口函数 `main()` 替代原有的 `if __name__ == "__main__"` 块。

---

### Task 5: 更新 pen.py 为薄入口

**Files:**
- Modify: `pen.py` — 整个文件替换为：

```python
#!/usr/bin/env python3
from pen.cli import main

if __name__ == "__main__":
    main()
```

---

## Phase 2: 八项优化

### Task 6: del 命令错误提示优化

**Files:**
- Modify: `pen/cli.py` — `delete_command` 函数

将现有的 `raise_for_status()` 改为解析服务端错误：

```python
@cli.command(name="del")
@click.argument("url")
def delete_command(url):
    """删除粘贴"""
    session = get_session()
    try:
        response = session.delete(f"{BASE_URL}/api/pastes/{url}")
        if response.status_code == 200:
            click.secho(f"成功删除 /{url}", fg="green")
        elif response.status_code == 401:
            result = response.json()
            msg = result.get("statusMessage", result.get("message", ""))
            click.secho(f"删除失败: {msg}", fg="red")
        else:
            result = response.json()
            msg = result.get("statusMessage", result.get("message", "未知错误"))
            click.secho(f"删除失败: {msg}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"删除失败: {str(e)}", fg="red")
```

---

### Task 7: 移除 pull 命令的 --address 无效参数

**Files:**
- Modify: `pen/cli.py` — `pull` 函数

删除 `@click.option("-a", "--address", help="服务器地址")` 装饰器行和函数参数 `address`。其他逻辑不变。

---

### Task 8: get_paste_content() 异常处理改进

**Files:**
- Modify: `pen/api.py` — `get_paste_content` 函数

将 `except: pass` 替换为区分网络错误和 HTTP 错误的处理：

```python
def get_paste_content(slug, session=None):
    if session is None:
        session = get_session()
    try:
        response = session.get(f"{BASE_URL}/api/pastes/{slug}")
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and "paste" in data:
                return data["paste"].get("contentRawMarkdown", "")
    except requests.exceptions.ConnectionError:
        pass
    except requests.exceptions.Timeout:
        pass
    except requests.exceptions.RequestException:
        pass
    return ""
```

**说明：** 区分了连接错误和超时（这两类明确是网络问题），其他异常一概吞掉返回空字符串（调用方不需要知道细节）。

---

### Task 9: add 命令添加 --expires-at

**Files:**
- Modify: `pen/cli.py` — `add` 函数

添加 `@click.option("--expires-at", default=None, help="过期时间 (ISO格式)")` 装饰器和函数参数，传递到 `set_paste_content`：

```python
@cli.command()
@click.argument("text")
@click.argument("url")
@click.option("--expires-at", default=None, help="过期时间 (ISO格式，如 2026-12-31T23:59:59.000Z)")
def add(text, url, expires_at):
    """在URL末尾追加文本"""
    session = get_session()
    try:
        existing_content = get_paste_content(url, session)
        if existing_content:
            new_content = existing_content.rstrip("\n") + "\n" + text
        else:
            new_content = text
        response = set_paste_content(url, new_content, session, expires_at=expires_at)
        response.raise_for_status()
        extra = f"，过期: {expires_at}" if expires_at else ""
        click.secho(f"成功添加到 /{url}{extra}", fg="green")
    except ValueError as e:
        click.secho(f"错误: {str(e)}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"添加失败: {str(e)}", fg="red")
        if hasattr(e, 'response') and e.response:
            try:
                click.echo(e.response.json())
            except:
                click.echo(e.response.text)
```

---

### Task 10: Shell 补全支持

**Files:**
- Modify: `pen/cli.py` — 添加 `completion` 命令

在 cli.py 中所有命令之后添加：

```python
@cli.command(name="completion")
def shell_completion():
    """生成 shell 自动补全脚本"""
    click.echo("# Pen shell completion")
    click.echo("# Add the following line to your shell config:\n")
    click.echo('# eval "$(_PEN_COMPLETE=bash_source pen)"   # bash')
    click.echo('# eval "$(_PEN_COMPLETE=zsh_source pen)"    # zsh')
    click.echo('# eval "$(_PEN_COMPLETE=fish_source pen)"   # fish')
```

同时更新 `help_command` 中的帮助文本，在末尾加上：
```
  completion
      生成 shell 自动补全脚本
```

---

### Task 11: REPL 添加 ls/cat 内建命令

**Files:**
- Modify: `pen/cli.py` — `run_interactive` 函数

在 cd/pwd 处理块之后，添加 ls 和 cat 支持：

```python
            if parts[0].lower() == 'ls':
                target = parts[1] if len(parts) > 1 else '.'
                target = os.path.expanduser(target)
                try:
                    items = os.listdir(target)
                    for item in sorted(items):
                        full = os.path.join(target, item)
                        suffix = "/" if os.path.isdir(full) else ""
                        click.echo(f"  {item}{suffix}")
                except FileNotFoundError:
                    click.secho(f"目录不存在: {target}", fg="red")
                except PermissionError:
                    click.secho(f"没有权限访问: {target}", fg="red")
                continue

            if parts[0].lower() == 'cat':
                if len(parts) < 2:
                    click.secho("用法: cat <file>", fg="yellow")
                    continue
                filepath = os.path.expanduser(parts[1])
                try:
                    text = read_file_text(filepath)
                    click.echo(text)
                except ValueError as e:
                    click.secho(f"错误: {str(e)}", fg="red")
                except FileNotFoundError:
                    click.secho(f"文件不存在: {filepath}", fg="red")
                continue
```

---

### Task 12: 创建 pytest 测试

**Files:**
- Create: `tests/__init__.py`（空文件）
- Create: `tests/test_utils.py`

```python
import os
import tempfile
import pytest
from pen.utils import validate_slug, read_file_text


class TestValidateSlug:
    def test_valid_slugs(self):
        assert validate_slug("abc") == (True, "")
        assert validate_slug("hello-world") == (True, "")
        assert validate_slug("test_123") == (True, "")
        assert validate_slug("a" * 48) == (True, "")

    def test_too_short(self):
        ok, msg = validate_slug("ab")
        assert ok is False
        assert "3-48" in msg

    def test_too_long(self):
        ok, msg = validate_slug("a" * 49)
        assert ok is False
        assert "3-48" in msg

    def test_invalid_chars(self):
        ok, msg = validate_slug("Hello")
        assert ok is False
        assert "a-z" in msg

        ok, msg = validate_slug("test space")
        assert ok is False

        ok, msg = validate_slug("test.123")
        assert ok is False

    def test_empty_string(self):
        ok, msg = validate_slug("")
        assert ok is False


class TestReadFileText:
    def test_read_utf8(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("hello world")
            path = f.name
        try:
            result = read_file_text(path)
            assert result == "hello world"
        finally:
            os.unlink(path)

    def test_read_chinese(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("你好世界")
            path = f.name
        try:
            result = read_file_text(path)
            assert result == "你好世界"
        finally:
            os.unlink(path)

    def test_binary_extension_rejected(self):
        with pytest.raises(ValueError, match="二进制文件"):
            read_file_text("test.png")

    def test_binary_content_rejected(self):
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            f.write(b"\x00" * 100 + b"text")
            path = f.name
        try:
            with pytest.raises(ValueError, match="二进制文件"):
                read_file_text(path)
        finally:
            os.unlink(path)
```

---

### Task 13: 更新 help 文本（聚合 Phase 2 新增功能）

**Files:**
- Modify: `pen/cli.py` — `help_command` 函数

在 help_text 中添加新的/变化的命令描述：
```
  add <text> <URL> [--expires-at <ISO>]
      在URL末尾追加文本，不存在则创建，可设过期时间

  pull <URL> [<filename>] [-o <filename>]
      拉取URL上的文本，默认保存到Desktop/URL.txt

  completion
      生成 shell 自动补全脚本
```

交互模式说明也要更新（ls、cat 支持）。

---

### Task 14: 编译验证 + 功能测试

**Files:**
- 运行: `pen.py help`, `pen.py status`, `pytest tests/`

- [ ] **Step 1: 运行导入检查**

```bash
cd E:/Desktop文件/pen/pen && python -c "from pen.cli import main; print('OK')"
```
预期：输出 OK，无 ImportError。

- [ ] **Step 2: 运行 help**

```bash
python pen.py help
```
预期：显示 v1.9.0，所有命令正确（包括 add --expires-at, completion, pull 无 --address）。

- [ ] **Step 3: 运行 status**

```bash
python pen.py status
```
预期：连接正常。

- [ ] **Step 4: 运行测试**

```bash
pip install pytest && cd E:/Desktop文件/pen/pen && python -m pytest tests/ -v
```
预期：所有 ValidateSlug 和 ReadFileText 测试 PASS。

- [ ] **Step 5: 测试 push/pull 端到端**

```bash
echo "optimization test" > test_opt.txt
python pen.py push test_opt.txt test-optimization
python pen.py pull test-optimization -o /tmp/pulled.txt
```
预期：推送成功，拉取内容一致。

- [ ] **Step 6: Commit**

```bash
git add pen.py pen/ tests/
git commit -m "refactor: split pen.py into package, add 8 optimizations

- Split into pen/ package (utils, api, cli)
- Improve del error messages with server status parsing
- Remove unused --address flag from pull
- Improve get_paste_content error handling
- Add --expires-at to add command
- Add shell completion command
- Add ls/cat to REPL interactive mode
- Add pytest unit tests for validate_slug and read_file_text"
```

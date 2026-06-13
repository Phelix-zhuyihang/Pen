# NetCut API 适配实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 更新 pen.py 以适配 paste.moxiao.site 更名为 NetCut 后的 API 变更，包括新的认证格式、过期时间功能、服务端登出等。

**Architecture:** 单文件修改 pen.py（~675 行），涉及基础设施层（set_paste_content）、业务逻辑层（认证流程）和 CLI 层（命令参数/输出）三个层次的变更。所有命令的 API 调用和响应解析集中修改。

**Tech Stack:** Python 3, Click, requests

---

### Task 1: VERSION 号与注册命令 (register)

**Files:**
- Modify: `pen.py:20`（VERSION）、`pen.py:164-188`（register 函数）、`pen.py:561-610`（help 文本）

- [ ] **Step 1: 更新 VERSION 号**

将第 20 行 `VERSION = "1.8.0"` 改为 `VERSION = "1.9.0"`。

- [ ] **Step 2: 更新 register 命令**

修改 `register` 函数，新增 `--email` / `-e` 可选参数，添加密码长度校验（最低 8 字符）。

将 register 函数（`pen.py:164-188`）替换为：

```python
@cli.command()
@click.argument("username")
@click.argument("password")
@click.option("-e", "--email", default=None, help="邮箱（可选）")
def register(username, password, email):
    """注册新用户"""
    if len(password) < 8:
        click.secho("密码长度至少 8 个字符", fg="red")
        return

    data = {"username": username, "password": password}
    if email:
        data["email"] = email

    session = requests.Session()
    try:
        response = session.post(f"{BASE_URL}/api/auth/register", json=data)
        result = response.json()

        if response.status_code == 200 and result.get("ok"):
            save_cookies(session, username)
            user = result.get("user", {})
            click.secho(f"注册成功！已登录为 {user.get('username', username)}", fg="green")
        elif response.status_code == 429:
            click.secho("操作过于频繁，请稍后再试", fg="red")
        else:
            msg = result.get("statusMessage", result.get("message", "未知错误"))
            click.secho(f"注册失败: {msg}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"注册失败: {str(e)}", fg="red")
        if hasattr(e, 'response') and e.response:
            try:
                click.echo(e.response.json())
            except:
                click.echo(e.response.text)
```

- [ ] **Step 3: 更新 help 文本中 register 的说明**

在 help_command 函数中，将 register 帮助行从：
```
  register <username> <password>
      注册新用户
```
改为：
```
  register <username> <password> [-e <email>]
      注册新用户，密码至少8位，可提供邮箱
```

---

### Task 2: login 命令响应格式适配

**Files:**
- Modify: `pen.py:189-213`（login 函数）

- [ ] **Step 1: 更新 login 命令响应解析**

将 login 函数（`pen.py:189-213`）替换为：

```python
@cli.command()
@click.argument("username")
@click.argument("password")
def login(username, password):
    """登录用户"""
    session = requests.Session()
    try:
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": username,
            "password": password
        })
        result = response.json()

        if response.status_code == 200 and result.get("ok"):
            save_cookies(session, username)
            user = result.get("user", {})
            click.secho(f"登录成功！欢迎 {user.get('username', username)}", fg="green")
        elif response.status_code == 429:
            click.secho("操作过于频繁，请稍后再试", fg="red")
        else:
            msg = result.get("statusMessage", result.get("message", "未知错误"))
            click.secho(f"登录失败: {msg}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"登录失败: {str(e)}", fg="red")
        if hasattr(e, 'response') and e.response:
            try:
                click.echo(e.response.json())
            except:
                click.echo(e.response.text)
```

---

### Task 3: logout 命令添加服务端登出

**Files:**
- Modify: `pen.py:402-410`（logout 函数）

- [ ] **Step 1: 更新 logout 命令**

将 logout 函数替换为：

```python
@cli.command()
def logout():
    """退出登录"""
    config = load_config()
    session = get_session()
    try:
        response = session.post(f"{BASE_URL}/api/auth/logout")
        if response.status_code == 200:
            click.secho("已从服务端退出登录", fg="green")
    except requests.exceptions.RequestException:
        pass
    if "cookies" in config:
        del config["cookies"]
    if "username" in config:
        del config["username"]
    save_config(config)
    click.secho("本地登录状态已清除", fg="green")
```

---

### Task 4: set_paste_content() 添加 expiresAt 支持

**Files:**
- Modify: `pen.py:122-140`（set_paste_content 函数）

- [ ] **Step 1: 更新 set_paste_content 函数签名和逻辑**

将 set_paste_content（`pen.py:122-140`）替换为：

```python
def set_paste_content(slug, content, session=None, visibility="public_read", expires_at=None):
    if session is None:
        session = get_session()
    is_valid, error_msg = validate_slug(slug)
    if not is_valid:
        raise ValueError(error_msg)

    check_response = session.get(f"{BASE_URL}/api/pastes/{slug}")
    exists = check_response.status_code == 200

    body = {
        "contentRawMarkdown": content,
        "visibility": visibility,
    }
    if expires_at:
        body["expiresAt"] = expires_at

    if exists:
        response = session.patch(f"{BASE_URL}/api/pastes/{slug}", json=body)
    else:
        body["customSlug"] = slug
        response = session.post(f"{BASE_URL}/api/pastes", json=body)
    return response
```

---

### Task 5: push 命令添加 --expires-at 选项

**Files:**
- Modify: `pen.py:242-277`（push 函数）、help 文本

- [ ] **Step 1: 更新 push 命令添加过期时间**

将 push 函数（`pen.py:242-277`）替换为：

```python
@cli.command()
@click.argument("file")
@click.argument("url")
@click.option("--force", is_flag=True, help="强制覆盖")
@click.option("-v", "--visibility", type=click.Choice(["public_read", "private"]), default="public_read", help="可见性")
@click.option("--expires-at", default=None, help="过期时间 (ISO格式，如 2026-12-31T23:59:59.000Z)")
def push(file, url, force, visibility, expires_at):
    """推送文件内容到URL"""
    file = os.path.abspath(os.path.expanduser(file))
    if not os.path.exists(file):
        click.secho(f"文件 {file} 不存在", fg="red")
        return
    try:
        content = read_file_text(file)
    except ValueError as e:
        click.secho(f"错误: {str(e)}", fg="red")
        return
    session = get_session()
    try:
        check_response = session.get(f"{BASE_URL}/api/pastes/{url}")
        exists = check_response.status_code == 200

        if exists and not force:
            click.secho(f"URL /{url} 已存在，使用 --force 参数强制覆盖", fg="yellow")
            return

        response = set_paste_content(url, content, session, visibility, expires_at)
        response.raise_for_status()
        extra = f"，过期: {expires_at}" if expires_at else ""
        click.secho(f"成功推送到 /{url} [{visibility}]{extra}", fg="green")
    except ValueError as e:
        click.secho(f"错误: {str(e)}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"推送失败: {str(e)}", fg="red")
        if hasattr(e, 'response') and e.response:
            try:
                click.echo(e.response.json())
            except:
                click.echo(e.response.text)
```

- [ ] **Step 2: 更新 help 文本 push 行**

将 push 帮助行改为：
```
  push <File> <URL> [--force] [-v public_read|private] [--expires-at <ISO>]
      推送文件内容到URL，--force强制覆盖，可设过期时间
```

---

### Task 6: open 命令适配 permissions 新格式

**Files:**
- Modify: `pen.py:357-400`（open 函数）

- [ ] **Step 1: 更新 open 命令**

将 open 函数（`pen.py:357-400`）替换为：

```python
@cli.command(name="open")
@click.argument("url")
@click.option("-r", is_flag=True, help="只读模式")
@click.option("-w", is_flag=True, help="写入模式")
def open_paste(url, r, w):
    """打开并（可选）编辑粘贴"""
    track_visit(url)
    session = get_session()
    try:
        response = session.get(f"{BASE_URL}/api/pastes/{url}")
        if response.status_code != 200:
            click.secho("URL不存在或无法访问", fg="yellow")
            return
        data = response.json()
        paste = data.get("paste", {})
        content = paste.get("contentRawMarkdown", "")
        permissions = data.get("permissions", {})

        if r or not w:
            if content:
                click.echo(content)
            else:
                click.secho("内容为空", fg="yellow")
        else:
            if not permissions.get("canEdit"):
                click.secho("你没有编辑此粘贴的权限", fg="red")
                return
            with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
                f.write(content)
                temp_name = f.name
            try:
                editor = os.environ.get("EDITOR", "notepad" if platform.system() == "Windows" else "nano")
                subprocess.call([editor, temp_name])
                with open(temp_name, "r", encoding="utf-8") as f:
                    new_content = f.read()
                session = get_session()
                response = set_paste_content(url, new_content, session)
                response.raise_for_status()
                click.secho(f"成功更新 /{url}", fg="green")
            except requests.exceptions.RequestException as e:
                click.secho(f"更新失败: {str(e)}", fg="red")
            finally:
                if os.path.exists(temp_name):
                    os.unlink(temp_name)
    except requests.exceptions.RequestException as e:
        click.secho(f"获取失败: {str(e)}", fg="red")
```

---

### Task 7: log 命令适配新响应格式

**Files:**
- Modify: `pen.py:314-355`（log 函数）

- [ ] **Step 1: 更新 log 命令显示 expired 字段**

将 log 函数中 paste 循环（`pen.py:333-351`）替换为：

```python
            for i, paste in enumerate(pastes, 1):
                slug = paste.get("id", "N/A")
                updated_at = paste.get("updatedAt", "N/A")
                visibility = paste.get("visibility", "N/A")
                expired = paste.get("expired", False)

                if updated_at != "N/A":
                    try:
                        dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                        updated_str = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        updated_str = updated_at
                else:
                    updated_str = updated_at

                click.echo(f"{i}. /{slug}")
                click.echo(f"   更新: {updated_str}")
                click.echo(f"   可见性: {visibility}")
                if expired:
                    click.secho(f"   状态: 已过期", fg="red")
                click.echo("")
```

---

### Task 8: clip 命令添加 --expires-at 选项

**Files:**
- Modify: `pen.py:472-514`（clip 函数）

- [ ] **Step 1: 更新 clip 命令**

将 clip 函数（`pen.py:472-514`）替换为：

```python
@cli.command()
@click.argument("url")
@click.option("--force", is_flag=True, help="强制覆盖")
@click.option("-v", "--visibility", type=click.Choice(["public_read", "private"]), default="public_read", help="可见性")
@click.option("--expires-at", default=None, help="过期时间 (ISO格式，如 2026-12-31T23:59:59.000Z)")
def clip(url, force, visibility, expires_at):
    """将剪贴板内容推送到URL"""
    try:
        import pyperclip
    except ImportError:
        click.secho("需要安装 pyperclip: pip install pyperclip", fg="red")
        return

    try:
        text = pyperclip.paste()
    except Exception as e:
        click.secho(f"无法读取剪贴板: {str(e)}", fg="red")
        return

    if not text:
        click.secho("剪贴板为空", fg="yellow")
        return

    session = get_session()
    try:
        check_response = session.get(f"{BASE_URL}/api/pastes/{url}")
        exists = check_response.status_code == 200

        if exists and not force:
            click.secho(f"URL /{url} 已存在，使用 --force 参数强制覆盖", fg="yellow")
            return

        response = set_paste_content(url, text, session, visibility, expires_at)
        response.raise_for_status()
        extra = f"，过期: {expires_at}" if expires_at else ""
        click.secho(f"成功将剪贴板内容推送到 /{url} [{visibility}]{extra}", fg="green")
    except ValueError as e:
        click.secho(f"错误: {str(e)}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"推送失败: {str(e)}", fg="red")
        if hasattr(e, 'response') and e.response:
            try:
                click.echo(e.response.json())
            except:
                click.echo(e.response.text)
```

---

### Task 9: help 文本全面更新

**Files:**
- Modify: `pen.py:561-610`（help_command 函数）

- [ ] **Step 1: 更新完整帮助文本**

将 help_command 函数中的 help_text 替换为：

```python
    help_text = """
Pen 命令行工具 v{}

命令列表:

  register <username> <password> [-e <email>]
      注册新用户，密码至少8位，可提供邮箱

  login <username> <password>
      登录用户

  push <File> <URL> [--force] [-v public_read|private] [--expires-at <ISO>]
      推送文件内容到URL，--force强制覆盖，可设过期时间

  pull <URL> [<filename>] [-o <filename>]
      拉取URL上的文本，默认保存到Desktop/URL.txt

  add <text> <URL>
      在URL末尾追加文本，不存在则创建

  del <URL>
      删除URL（需登录且为创建者）

  log
      显示用户创建的所有粘贴列表

  open <URL> [-r | -w]
      打开URL，-r只读（默认），-w编辑

  surf <URL>
      在浏览器中打开粘贴页面

  clip <URL> [--force] [-v public_read|private] [--expires-at <ISO>]
      将剪贴板内容推送到URL

  logout
      退出登录（同步清除服务端和本地状态）

  status
      显示状态信息（登录状态、连接情况、延迟、访问记录）

  init
      将pen添加到系统PATH环境变量

  help
      显示此帮助信息
""".format(VERSION)
```

---

### Task 10: 验证测试

**Files:**
- 运行: `python pen.py`（现有测试脚本 + 手工验证）

- [ ] **Step 1: 运行 help 确认文本正确**

```bash
pipenv run python pen.py help
```
或
```bash
python pen.py help
```
预期：显示 v1.9.0，所有命令参数与计划一致。

- [ ] **Step 2: 运行 status 确认连接正常**

```bash
python pen.py status
```
预期：连接状态正常，显示 v1.9.0。

- [ ] **Step 3: 测试注册密码校验**

尝试用短密码注册（预期被拦截）：
```bash
python pen.py register test_user abcd123
```
预期输出：密码长度至少 8 个字符。

- [ ] **Step 4: 测试 push 带 expires-at**

```bash
echo "hello expire test" > /tmp/test_expire.txt
python pen.py push /tmp/test_expire.txt test-expire --expires-at "2027-01-01T00:00:00.000Z"
```
预期：推送成功，输出中包含过期时间。

- [ ] **Step 5: 测试 pull 确认内容正确**

```bash
python pen.py pull test-expire
```
预期：拉取成功，内容为 "hello expire test"。

- [ ] **Step 6: Commit**

```bash
git add pen.py docs/superpowers/plans/2026-06-13-netcut-api-update.md
git commit -m "feat: adapt to NetCut API changes (v1.9.0)

- register: add --email option, password min 8 chars
- login/logout: add server-side logout, better error messages
- push/clip: add --expires-at option
- log: show expired status
- open: adapt to new permissions format
- set_paste_content: support expiresAt field"
```

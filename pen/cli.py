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


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        help_command()
    pass


@cli.command()
@click.argument("username")
@click.argument("password")
@click.option("-e", "--email", default=None, help="邮箱（可选）")
def register(username, password, email):
    """注册新用户"""
    if len(password) < 8:
        click.secho("✗ 密码长度至少 8 个字符", fg="red")
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
            click.secho(f"✓ 注册成功！已登录为 {user.get('username', username)}", fg="green")
        elif response.status_code == 429:
            click.secho("⚠ 操作过于频繁，请稍后再试", fg="red")
        else:
            msg = result.get("statusMessage", result.get("message", "未知错误"))
            click.secho(f"✗ 注册失败: {msg}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"✗ 注册失败: {str(e)}", fg="red")
        if hasattr(e, 'response') and e.response:
            try:
                click.echo(e.response.json())
            except:
                click.echo(e.response.text)


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
            click.secho(f"✓ 登录成功！欢迎 {user.get('username', username)}", fg="green")
        elif response.status_code == 429:
            click.secho("⚠ 操作过于频繁，请稍后再试", fg="red")
        else:
            msg = result.get("statusMessage", result.get("message", "未知错误"))
            click.secho(f"✗ 登录失败: {msg}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"✗ 登录失败: {str(e)}", fg="red")
        if hasattr(e, 'response') and e.response:
            try:
                click.echo(e.response.json())
            except:
                click.echo(e.response.text)


@cli.command()
@click.argument("url")
@click.argument("file", required=False)
@click.option("-o", "--output", help="输出文件名")
def pull(url, file, output):
    try:
        content = get_paste_content(url)
        if content == "":
            click.secho(f"⚠ 无法获取内容或URL不存在: {url}", fg="yellow")
            return

        if output:
            output_path = output
        elif file:
            output_path = file
        else:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            if not os.path.exists(desktop):
                desktop = os.path.expanduser("~")
            output_path = os.path.join(desktop, f"{url}.txt")
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        click.secho(f"✓ 成功拉取到 {output_path}", fg="green")
    except requests.exceptions.RequestException as e:
        click.secho(f"✗ 拉取失败: {str(e)}", fg="red")


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
        click.secho(f"✗ 文件 {file} 不存在", fg="red")
        return
    try:
        content = read_file_text(file)
    except ValueError as e:
        click.secho(f"✗ 错误: {str(e)}", fg="red")
        return
    session = get_session()
    try:
        check_response = session.get(f"{BASE_URL}/api/pastes/{url}")
        exists = check_response.status_code == 200

        if exists and not force:
            click.secho(f"⚠ URL /{url} 已存在，使用 --force 参数强制覆盖", fg="yellow")
            return

        response = set_paste_content(url, content, session, visibility, expires_at)
        response.raise_for_status()
        extra = f"，过期: {expires_at}" if expires_at else ""
        click.secho(f"✓ 成功推送到 /{url} [{visibility}]{extra}", fg="green")
    except ValueError as e:
        click.secho(f"✗ 错误: {str(e)}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"✗ 推送失败: {str(e)}", fg="red")
        if hasattr(e, 'response') and e.response:
            try:
                click.echo(e.response.json())
            except:
                click.echo(e.response.text)


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
        click.secho(f"✓ 成功添加到 /{url}{extra}", fg="green")
    except ValueError as e:
        click.secho(f"✗ 错误: {str(e)}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"✗ 添加失败: {str(e)}", fg="red")
        if hasattr(e, 'response') and e.response:
            try:
                click.echo(e.response.json())
            except:
                click.echo(e.response.text)


@cli.command(name="del")
@click.argument("url")
def delete_command(url):
    """删除粘贴"""
    session = get_session()
    try:
        response = session.delete(f"{BASE_URL}/api/pastes/{url}")
        if response.status_code == 200:
            click.secho(f"✓ 成功删除 /{url}", fg="green")
        elif response.status_code == 401:
            result = response.json()
            msg = result.get("statusMessage", result.get("message", ""))
            click.secho(f"✗ 删除失败: {msg}", fg="red")
        else:
            result = response.json()
            msg = result.get("statusMessage", result.get("message", "未知错误"))
            click.secho(f"✗ 删除失败: {msg}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"✗ 删除失败: {str(e)}", fg="red")


@cli.command()
def log():
    config = load_config()
    if "username" not in config:
        click.secho("⚠ 请先登录", fg="red")
        return

    session = get_session()
    try:
        response = session.get(f"{BASE_URL}/api/pastes/mine")
        if response.status_code == 401:
            click.secho("✗ 登录已过期，请重新登录", fg="red")
            return
        if response.status_code != 200:
            click.secho(f"✗ 获取失败: {response.status_code}", fg="red")
            return
        data = response.json()

        if data.get("ok") and "pastes" in data:
            pastes = data["pastes"]
            if not pastes:
                click.secho("⚠ 暂无粘贴", fg="yellow")
                return

            click.echo(f"\n{click.style(' 找到 ' + str(len(pastes)) + ' 个粘贴', fg='cyan', bold=True)}\n")
            # Header
            header = f"  {'#':<3} {'SLUG':<20} {'更新':<18} {'可见性':<12} {'状态'}"
            click.secho(header, fg="bright_black", bold=True)
            click.secho(f"  {'─'*3} {'─'*20} {'─'*18} {'─'*12} {'─'*6}", fg="bright_black")
            for i, paste in enumerate(pastes, 1):
                slug = paste.get("id", "N/A")
                if len(slug) > 18:
                    slug = slug[:17] + "…"
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

                vis_str = "公开" if visibility == "public_read" else "私有"
                status_str = click.style("已过期", fg="red") if expired else click.style("正常", fg="green")

                row = f"  {i:<3} {slug:<20} {updated_str:<18} {vis_str:<12} "
                click.echo(row, nl=False)
                click.echo(status_str)
            click.echo("")
        else:
            click.secho("✗ 获取失败", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"✗ 获取失败: {str(e)}", fg="red")


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
            click.secho("⚠ URL不存在或无法访问", fg="yellow")
            return
        data = response.json()
        paste = data.get("paste", {})
        content = paste.get("contentRawMarkdown", "")
        permissions = data.get("permissions", {})

        if r or not w:
            if content:
                click.echo(content)
            else:
                click.secho("⚠ 内容为空", fg="yellow")
        else:
            if not permissions.get("canEdit"):
                click.secho("✗ 你没有编辑此粘贴的权限", fg="red")
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
                click.secho(f"✓ 成功更新 /{url}", fg="green")
            except requests.exceptions.RequestException as e:
                click.secho(f"✗ 更新失败: {str(e)}", fg="red")
            finally:
                if os.path.exists(temp_name):
                    os.unlink(temp_name)
    except requests.exceptions.RequestException as e:
        click.secho(f"✗ 获取失败: {str(e)}", fg="red")


@cli.command()
def logout():
    """退出登录"""
    config = load_config()
    session = get_session()
    try:
        response = session.post(f"{BASE_URL}/api/auth/logout")
        if response.status_code == 200:
            click.secho("✓ 已从服务端退出登录", fg="green")
    except requests.exceptions.RequestException:
        pass
    if "cookies" in config:
        del config["cookies"]
    if "username" in config:
        del config["username"]
    save_config(config)
    click.secho("✓ 本地登录状态已清除", fg="green")


@cli.command()
def status():
    """显示状态信息"""
    sep = click.style("─" * 40, fg="bright_black")

    click.secho(f"\n{' Pen v' + VERSION + ' ':=^40}", fg="cyan", bold=True)
    click.echo(f"  时间:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo(f"  服务器: {BASE_URL}")

    # ── 账户 ──
    click.echo(f"\n{sep}")
    click.secho("  账户", fg="cyan", bold=True)
    config = load_config()
    if "username" in config:
        session = get_session()
        try:
            me_response = session.get(f"{BASE_URL}/api/auth/me")
            if me_response.status_code == 200:
                data = me_response.json()
                if data.get("loggedIn"):
                    click.secho(f"  ✓ 已登录 ({config['username']})", fg="green")
                else:
                    click.secho(f"  ✗ 已过期，请重新登录", fg="red")
            else:
                click.secho(f"  ✗ 已过期，请重新登录", fg="red")
        except:
            click.secho(f"  ✗ 已过期，请重新登录", fg="red")
    else:
        click.secho(f"  ⚠ 未登录", fg="yellow")

    # ── 连接 ──
    click.echo(f"\n{sep}")
    click.secho("  连接", fg="cyan", bold=True)
    try:
        start = time.time()
        ping_resp = requests.get(BASE_URL, timeout=5)
        latency = (time.time() - start) * 1000
        if ping_resp.status_code == 200 or ping_resp.status_code == 302 or ping_resp.status_code == 301:
            click.secho(f"  ✓ 正常  ({latency:.0f}ms)", fg="green")
        else:
            click.secho(f"  ✗ 异常  ({latency:.0f}ms, {ping_resp.status_code})", fg="red")
    except requests.exceptions.ConnectionError:
        click.secho(f"  ✗ 无法连接", fg="red")
    except requests.exceptions.Timeout:
        click.secho(f"  ✗ 连接超时", fg="red")
    except Exception as e:
        click.secho(f"  ✗ 错误 ({str(e)})", fg="red")

    # ── 历史 ──
    click.echo(f"\n{sep}")
    click.secho("  访问记录", fg="cyan", bold=True)
    visited = config.get("visited", [])
    if visited:
        for v in reversed(visited[-10:]):
            click.echo(f"  /{v['slug']:<20} {v['time']}")
    else:
        click.secho(f"  (无)", fg="bright_black")
    click.echo("")


@cli.command()
@click.argument("slug")
def surf(slug):
    track_visit(slug)
    url = f"{BASE_URL}/p/{slug}"
    click.secho(f"正在打开 {url} ...", fg="cyan")
    webbrowser.open(url)


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
        click.secho("✗ 需要安装 pyperclip: pip install pyperclip", fg="red")
        return

    try:
        text = pyperclip.paste()
    except Exception as e:
        click.secho(f"✗ 无法读取剪贴板: {str(e)}", fg="red")
        return

    if not text:
        click.secho("⚠ 剪贴板为空", fg="yellow")
        return

    session = get_session()
    try:
        check_response = session.get(f"{BASE_URL}/api/pastes/{url}")
        exists = check_response.status_code == 200

        if exists and not force:
            click.secho(f"⚠ URL /{url} 已存在，使用 --force 参数强制覆盖", fg="yellow")
            return

        response = set_paste_content(url, text, session, visibility, expires_at)
        response.raise_for_status()
        extra = f"，过期: {expires_at}" if expires_at else ""
        click.secho(f"✓ 成功将剪贴板内容推送到 /{url} [{visibility}]{extra}", fg="green")
    except ValueError as e:
        click.secho(f"✗ 错误: {str(e)}", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"✗ 推送失败: {str(e)}", fg="red")
        if hasattr(e, 'response') and e.response:
            try:
                click.echo(e.response.json())
            except:
                click.echo(e.response.text)


@cli.command()
def init():
    if platform.system() == "Windows":
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_ALL_ACCESS)
        try:
            path, _ = winreg.QueryValueEx(key, "Path")
        except WindowsError:
            path = ""

        if getattr(sys, 'frozen', False):
            exe_path = os.path.dirname(sys.executable)
            target_dir = exe_path
            msg = "pen.exe"
        else:
            target_dir = os.path.dirname(os.path.abspath(__file__))
            msg = "pen.py"

        target_dir = os.path.normpath(target_dir)

        click.echo(f"检测到的目录: {target_dir}")
        display_path = path[:100] + "..." if len(path) > 100 else path
        click.echo(f"当前PATH: {display_path}")
        click.echo("")

        path_dirs = path.split(";")
        found = False
        for d in path_dirs:
            d = os.path.normpath(d) if d else d
            if d and d.lower() == target_dir.lower():
                found = True
                break

        if not found:
            new_path = path + ";" + target_dir if path else target_dir
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
            click.secho(f"已将{msg}所在目录添加到PATH环境变量！", fg="green")
            click.secho("请重启终端生效。", fg="cyan")
        else:
            click.secho("已经在PATH中！", fg="yellow")
            click.secho(f"目录: {target_dir}", fg="cyan")
        winreg.CloseKey(key)
    else:
        click.echo("请手动将pen.py所在目录添加到PATH环境变量")


@cli.command(name="help")
def help_command():
    """显示帮助"""
    B = click.style  # shorthand
    sep = B("─" * 44, fg="bright_black")

    click.echo("")
    click.secho(f"  Pen 命令行工具 v{VERSION}", fg="cyan", bold=True)
    click.echo("")

    click.secho("  账户", fg="cyan", bold=True)
    click.echo(sep)
    click.echo(f"  {B('register', 'green'):<30} 注册新用户（密码至少8位）")
    click.echo(f"  {B('login', 'green'):<30} 登录用户")
    click.echo(f"  {B('logout', 'green'):<30} 退出登录")
    click.echo("")

    click.secho("  粘贴", fg="cyan", bold=True)
    click.echo(sep)
    click.echo(f"  {B('push', 'green'):<30} 推送文件到URL [--force] [--expires-at]")
    click.echo(f"  {B('pull', 'green'):<30} 拉取URL内容到本地")
    click.echo(f"  {B('add', 'green'):<30} 追加文本到URL [--expires-at]")
    click.echo(f"  {B('del', 'green'):<30} 删除URL")
    click.echo(f"  {B('open', 'green'):<30} 打开并编辑 [-r 只读 | -w 写入]")
    click.echo(f"  {B('surf', 'green'):<30} 浏览器打开粘贴页面")
    click.echo(f"  {B('clip', 'green'):<30} 推送剪贴板内容 [--expires-at]")
    click.echo(f"  {B('log', 'green'):<30} 列出我的所有粘贴")
    click.echo("")

    click.secho("  系统", fg="cyan", bold=True)
    click.echo(sep)
    click.echo(f"  {B('status', 'green'):<30} 显示登录/连接/访问记录")
    click.echo(f"  {B('init', 'green'):<30} 添加到系统 PATH")
    click.echo(f"  {B('completion', 'green'):<30} 生成 shell 补全脚本")
    click.echo(f"  {B('help', 'green'):<30} 显示此帮助")
    click.echo("")


@cli.command(name="completion")
def shell_completion():
    """生成 shell 自动补全脚本"""
    click.echo("# Pen shell completion")
    click.echo("# Add the following line to your shell config:\n")
    click.echo('# eval("$(_PEN_COMPLETE=bash_source pen)")   # bash')
    click.echo('# eval("$(_PEN_COMPLETE=zsh_source pen)")    # zsh')
    click.echo('# eval("$(_PEN_COMPLETE=fish_source pen)")   # fish')


def run_interactive():
    click.secho(f"Pen 命令行工具 v{VERSION}", fg="cyan", bold=True)
    click.echo("内建命令: cd, pwd, ls, cat, exit")
    click.echo("输入命令（输入 exit 或 quit 退出）:\n")

    while True:
        try:
            cwd = os.getcwd()
            home = os.path.expanduser("~")
            if cwd.lower() == home.lower():
                display_dir = "~"
            else:
                display_dir = os.path.basename(cwd) or cwd

            config = load_config()
            username = config.get("username", None)
            if username:
                click.echo(click.style(username, fg="green") +
                           click.style("@pen", fg="bright_black") + " " +
                           click.style(display_dir, fg="yellow") +
                           click.style("> ", fg="bright_black"), nl=False)
            else:
                click.echo(click.style("pen", fg="cyan") + " " +
                           click.style(display_dir, fg="yellow") +
                           click.style("> ", fg="bright_black"), nl=False)
            sys.stdout.flush()
            user_input = input().strip()
            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("再见！")
                break

            parts = shlex.split(user_input)
            if not parts:
                continue

            if parts[0].lower() == 'cd':
                if len(parts) < 2:
                    target = os.path.expanduser("~")
                else:
                    target = os.path.expanduser(parts[1])
                try:
                    os.chdir(target)
                    click.secho(f"→ {os.getcwd()}", fg="cyan")
                except FileNotFoundError:
                    click.secho(f"目录不存在: {target}", fg="red")
                except NotADirectoryError:
                    click.secho(f"不是目录: {target}", fg="red")
                except PermissionError:
                    click.secho(f"没有权限访问: {target}", fg="red")
                continue

            if parts[0].lower() == 'pwd':
                click.echo(os.getcwd())
                continue

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
                    click.secho(f"✗ 错误: {str(e)}", fg="red")
                except FileNotFoundError:
                    click.secho(f"文件不存在: {filepath}", fg="red")
                continue

            cmd_args = ['pen'] + parts
            old_argv = sys.argv
            sys.argv = cmd_args
            try:
                cli()
            except SystemExit:
                pass
            sys.argv = old_argv
        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print(f"错误: {e}")


def main():
    if len(sys.argv) == 1:
        run_interactive()
    else:
        cli()

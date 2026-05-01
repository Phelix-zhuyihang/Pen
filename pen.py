#!/usr/bin/env python3
import click
import requests
import json
import os
import sys
from datetime import datetime
import tempfile
import subprocess
import platform

VERSION = "1.4.0"
BASE_URL = "https://server.moxiao.site"
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".pen_config.json")

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

def get_paste_content(slug):
    try:
        response = requests.get(f"{BASE_URL}/api/pastes/{slug}")
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and "paste" in data:
                return data["paste"].get("contentRawMarkdown", "")
    except:
        pass
    return ""

def set_paste_content(slug, content, session=None):
    if session is None:
        session = get_session()
    try:
        check_response = session.get(f"{BASE_URL}/api/pastes/{slug}")
        exists = check_response.status_code == 200

        if exists:
            response = session.patch(f"{BASE_URL}/api/pastes/{slug}", json={"contentRawMarkdown": content})
        else:
            response = session.post(f"{BASE_URL}/api/pastes", json={
                "customSlug": slug,
                "contentRawMarkdown": content,
                "visibility": "public_read"
            })
        return response
    except Exception as e:
        raise e

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        help_command()
    pass

@cli.command()
@click.argument("username")
@click.argument("password")
@click.option("-email", help="邮箱（可选）")
def register(username, password, email):
    data = {"username": username, "password": password}
    if email:
        data["email"] = email

    session = requests.Session()
    try:
        response = session.post(f"{BASE_URL}/api/auth/register", json=data)
        response.raise_for_status()
        result = response.json()

        if result.get("ok"):
            save_cookies(session, username)
            click.secho(f"注册成功！已登录为 {username}", fg="green")
        else:
            click.secho("注册成功！", fg="green")
    except requests.exceptions.RequestException as e:
        click.secho(f"注册失败: {str(e)}", fg="red")
        if hasattr(e, 'response') and e.response:
            try:
                click.echo(e.response.json())
            except:
                click.echo(e.response.text)

@cli.command()
@click.argument("username")
@click.argument("password")
def login(username, password):
    session = requests.Session()
    try:
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "identifier": username,
            "password": password
        })
        response.raise_for_status()
        result = response.json()

        if result.get("ok"):
            save_cookies(session, username)
            click.secho(f"登录成功！欢迎 {username}", fg="green")
        else:
            click.secho("登录成功！", fg="green")
    except requests.exceptions.RequestException as e:
        click.secho(f"登录失败: {str(e)}", fg="red")
        if hasattr(e, 'response') and e.response:
            try:
                click.echo(e.response.json())
            except:
                click.echo(e.response.text)

@cli.command()
@click.argument("url")
@click.argument("file", required=False)
@click.option("-o", "--output", help="输出文件名")
@click.option("-a", "--address", help="服务器地址")
def pull(url, file, output, address):
    try:
        content = get_paste_content(url)
        if content == "":
            click.secho(f"无法获取内容或URL不存在: {url}", fg="yellow")
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
        click.secho(f"成功拉取到 {output_path}", fg="green")
    except requests.exceptions.RequestException as e:
        click.secho(f"拉取失败: {str(e)}", fg="red")

@cli.command()
@click.argument("file")
@click.argument("url")
@click.option("-force", is_flag=True, help="强制覆盖")
def push(file, url, force):
    if not os.path.exists(file):
        click.secho(f"文件 {file} 不存在", fg="red")
        return
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
    session = get_session()
    try:
        check_response = session.get(f"{BASE_URL}/api/pastes/{url}")
        exists = check_response.status_code == 200

        if exists and not force:
            click.secho(f"URL /{url} 已存在，使用 -force 参数强制覆盖", fg="yellow")
            return

        response = set_paste_content(url, content, session)
        response.raise_for_status()
        click.secho(f"成功推送到 /{url}", fg="green")
    except requests.exceptions.RequestException as e:
        click.secho(f"推送失败: {str(e)}", fg="red")
        if hasattr(e, 'response') and e.response:
            try:
                click.echo(e.response.json())
            except:
                click.echo(e.response.text)

@cli.command()
@click.argument("text")
@click.argument("url")
def add(text, url):
    session = get_session()
    try:
        existing_content = get_paste_content(url)
        new_content = existing_content + "\n" + text if existing_content else text
        response = set_paste_content(url, new_content, session)
        response.raise_for_status()
        click.secho(f"成功添加到 /{url}", fg="green")
    except requests.exceptions.RequestException as e:
        click.secho(f"添加失败: {str(e)}", fg="red")

@cli.command(name="del")
@click.argument("url")
def delete_command(url):
    session = get_session()
    try:
        response = session.delete(f"{BASE_URL}/api/pastes/{url}")
        response.raise_for_status()
        click.secho(f"成功删除 /{url}", fg="green")
    except requests.exceptions.RequestException as e:
        click.secho(f"删除失败: {str(e)}", fg="red")

@cli.command()
def log():
    config = load_config()
    if "username" not in config:
        click.secho("请先登录", fg="red")
        return

    session = get_session()
    try:
        response = session.get(f"{BASE_URL}/api/pastes/mine")
        response.raise_for_status()
        data = response.json()

        if data.get("ok") and "pastes" in data:
            pastes = data["pastes"]
            if not pastes:
                click.secho("暂无粘贴", fg="yellow")
                return

            click.echo(f"找到 {len(pastes)} 个粘贴:\n")
            for i, paste in enumerate(pastes, 1):
                slug = paste.get("id", "N/A")
                updated_at = paste.get("updatedAt", "N/A")
                visibility = paste.get("visibility", "N/A")

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
                click.echo("")
        else:
            click.secho("获取失败", fg="red")
    except requests.exceptions.RequestException as e:
        click.secho(f"获取失败: {str(e)}", fg="red")

@cli.command(name="open")
@click.argument("url")
@click.option("-r", is_flag=True, help="只读模式")
@click.option("-w", is_flag=True, help="写入模式")
def open_paste(url, r, w):
    try:
        content = get_paste_content(url)
        if r or not w:
            if content:
                click.echo(content)
            else:
                click.secho("URL不存在或内容为空", fg="yellow")
        else:
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

@cli.command()
def logout():
    config = load_config()
    if "cookies" in config:
        del config["cookies"]
    if "username" in config:
        del config["username"]
    save_config(config)
    click.secho("已退出登录", fg="green")

@cli.command()
def status():
    click.echo(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo(f"版本: {VERSION}")

    config = load_config()
    if "username" in config:
        session = get_session()
        try:
            me_response = session.get(f"{BASE_URL}/api/auth/me")
            if me_response.status_code == 200:
                data = me_response.json()
                if data.get("loggedIn"):
                    click.secho(f"登录状态: 已登录 ({config['username']})", fg="green")
                else:
                    click.secho("登录状态: 已过期，请重新登录", fg="yellow")
            else:
                click.secho("登录状态: 已过期，请重新登录", fg="yellow")
        except:
            click.secho("登录状态: 已过期，请重新登录", fg="yellow")
    else:
        click.secho("登录状态: 未登录", fg="yellow")

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
    help_text = """
Pen 命令行工具 v{}

命令列表:

  register <username> <password> [-email <email>]
      注册新用户

  login <username> <password>
      登录用户

  pull <URL> [<filename>] [-o <filename>]
      拉取URL上的文本，默认保存到Desktop/URL.txt

  push <File> <URL> [-force]
      推送文件内容到URL，-force强制覆盖

  add <text> <URL>
      在URL末尾添加文本，不存在则创建

  del <URL>
      删除URL

  log
      显示用户创建的所有粘贴列表

  open <URL> [-r/-w]
      打开URL编辑，-r只读，-w写入

  logout
      退出登录

  status
      显示状态信息

  init
      添加到PATH环境变量

  help
      显示此帮助信息
""".format(VERSION)
    click.echo(help_text)

def run_interactive():
    print(f"Pen 命令行工具 v{VERSION}")
    print("输入命令（输入 exit 或 quit 退出）:\n")

    while True:
        try:
            user_input = input("pen> ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("再见！")
                break

            parts = user_input.split()
            if parts:
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

if __name__ == "__main__":
    if len(sys.argv) == 1:
        run_interactive()
    else:
        cli()


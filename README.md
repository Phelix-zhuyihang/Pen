# Pen - NetCut 粘贴板命令行工具

[![Release](https://img.shields.io/badge/version-v1.4.0-blue.svg)](https://github.com/) 
[![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen.svg)](https://www.python.org/) 
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)]()

## 简介

Pen 是一个用于与 **server.moxiao.site** 粘贴板网站交互的命令行工具。它提供了完整的注册、登录、推送、拉取、编辑等功能。

## 特性

- 🚀 快速的命令行操作
- 🔐 安全的 Cookie 会话管理
- 📄 支持文件推送到粘贴板
- ✏️ 内置文本编辑器功能
- 🌐 支持自定义服务器地址
- 📊 自动记录和管理你的粘贴板

## 安装

### 方法1: 使用可执行文件 (推荐)

1. 下载最新的 `pen.exe` 发布版本
2. 运行 `pen init` 添加到系统 PATH
3. 重启终端后即可使用

### 方法2: 使用 Python 运行

```bash
# 克隆仓库
git clone https://github.com/your-name/pen.git
cd pen

# 安装依赖
pip install -r requirements.txt

# 运行
python pen.py help
```

### 方法3: 编译为 exe

```bash
# 运行构建脚本
pyinstaller --onefile --name pen pen.py

# 编译后的文件在 dist/pen.exe
```

## 命令列表

### 注册

```bash
pen register <username> <password> [ -email <email> ]
```

**示例:**
```bash
pen register myuser mypassword
pen register myuser mypassword -email me@example.com
```

### 登录

```bash
pen login <username> <password>
```

**示例:**
```bash
pen login myuser mypassword
```

### 拉取

```bash
pen pull <URL> [ <filename> ] [ -o <filename> ] [ -a <address> ]
```

将指定 URL 的文本拉取下来，默认保存到桌面。

**示例:**
```bash
pen pull mypage
pen pull mypage C:\Documents\mypage.txt
pen pull mypage -o C:\Documents\mypage.txt
```

### 推送

```bash
pen push <File> <URL> [ -force ]
```

将文件内容推送到指定 URL，-force 参数可以强制覆盖已存在的内容。

**示例:**
```bash
pen push myfile.txt mypage
pen push myfile.txt mypage -force
```

### 添加

```bash
pen add <text> <URL>
```

在指定 URL 末尾添加文本，如果 URL 不存在则创建。

**示例:**
```bash
pen add "这是追加的文本" mypage
```

### 删除

```bash
pen del <URL>
```

**示例:**
```bash
pen del mypage
```

### 日志

```bash
pen log
```

显示用户创建的所有粘贴板列表。

### 打开编辑

```bash
pen open <URL> [ -r | -w ]
```

- `-r` 只读模式（默认）
- `-w` 写入模式

**示例:**
```bash
pen open mypage          # 只读显示
pen open mypage -w       # 用编辑器打开编辑
```

### 退出登录

```bash
pen logout
```

### 状态

```bash
pen status
```

显示当前时间、版本和登录状态。

### 添加到 PATH

```bash
pen init
```

将 pen.exe 所在目录添加到系统 PATH 环境变量（Windows）。

### 帮助

```bash
pen help
```

显示所有可用命令。

## 配置文件

配置文件保存在 `~/.pen_config.json`，包含：

- 登录会话的 Cookies
- 当前登录用户名

## 项目结构

```
pen/
├── pen.py              # 主程序源码
├── requirements.txt    # Python 依赖
├── README.md          # 说明文档
├── LICENSE            # 许可证 (可选)
└── .gitignore         # Git 忽略配置
```

## 开发

### 依赖

- `Click` - 命令行界面
- `Requests` - HTTP 请求

### 安装开发依赖

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
python pen.py status
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

[MIT License](LICENSE)

## 致谢

- [NetCut](https://server.moxiao.site) - 提供粘贴板服务
- [Click](https://click.palletsprojects.com) - 命令行框架
- [Requests](https://requests.readthedocs.io) - HTTP 库

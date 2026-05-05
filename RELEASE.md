# Pen 项目发布指南

## 前置准备

### 1. 安装 Git

下载地址: https://git-scm.com/download/win

### 2. 注册账号

- **GitHub**: https://github.com/signup
- **Gitee**: https://gitee.com/signup

### 3. 创建远程仓库

#### 在 GitHub 创建
1. 访问 https://github.com/new
2. 输入仓库名 `pen`
3. 选择 Public（公开）或 Private（私有）
4. 不要勾选 Initialize this repository with...
5. 点击 Create repository

#### 在 Gitee 创建
1. 访问 https://gitee.com/projects/new
2. 输入仓库名 `pen`
3. 选择 公开 或 私有
4. 点击 创建

## 步骤1: 初始化本地仓库

```bash
cd c:\Users\Administrator\Desktop\pen
git init
git add .
git commit -m "Initial commit"
```

## 步骤2: 关联远程仓库

### GitHub
```bash
git remote add origin https://github.com/你的用户名/pen.git
```

### Gitee
```bash
git remote add origin https://gitee.com/你的用户名/pen.git
```

## 步骤3: 推送代码

```bash
git push -u origin master
```
（或 git push -u origin main，取决于默认分支名）

## 步骤4: 发布 Release

### 在 GitHub 发布

1. 访问你的仓库
2. 点击 Releases
3. 点击 Draft a new release
4. 填写版本信息:
   - **Tag version**: v1.5.1
   - **Release title**: Pen v1.5.1
   - **Description**: 更新说明
5. 上传文件:
   - `dist/pen.exe`
   - `installer/pen-setup.exe` (如果有的话)
6. 点击 Publish release

### 在 Gitee 发布

1. 访问你的仓库
2. 点击 发行版
3. 点击 发布新版本
4. 填写信息并上传文件

## 步骤5: 创建安装程序（可选）

### 安装 Inno Setup

下载: https://jrsoftware.org/isdl.php#stable

### 编译安装程序

```bash
# 先构建 exe
pyinstaller --onefile --name pen pen.py

# 然后运行构建脚本
build_all.bat
# 或手动编译
iscc pen.iss
```

## 项目文件说明

```
pen/
├── pen.py              # 主程序
├── requirements.txt    # 依赖
├── README.md          # 说明文档
├── LICENSE            # 许可证
├── .gitignore         # Git 配置
├── ICON.md            # 图标指南
├── build_all.bat      # 构建工具
├── pen.iss            # Inno Setup 脚本
└── dist/              # 编译输出 (不提交到Git)
    └── pen.exe
```

## Git 使用备忘单

```bash
# 查看状态
git status

# 添加文件
git add .

# 提交更改
git commit -m "描述你的更改"

# 推送
git push

# 拉取更新
git pull

# 查看历史
git log

# 查看远程仓库
git remote -v
```

## 常见问题

### Q: 如何添加图标？

A: 参考 ICON.md 文档，下载或制作 icon.ico，然后修改打包命令:
```bash
pyinstaller --onefile --name pen --icon icon.ico pen.py
```

### Q: 如何更新版本？

A:
1. 修改 pen.py 中的 VERSION
2. 修改 README.md 中的版本号
3. 修改 pen.iss 中的版本号
4. Git 提交并推送
5. 发布新的 Release

### Q: dist 文件夹是否应该提交？

A: 不应该。dist 是构建产物，已经加入了 .gitignore。用户通过 Release 页面下载。

## 下一步建议

- [ ] 制作一个简单的图标
- [ ] 添加更多测试用例
- [ ] 写一个中文博客介绍项目
- [ ] 邀请朋友使用和反馈
- [ ] 考虑添加 GitHub Actions 自动构建

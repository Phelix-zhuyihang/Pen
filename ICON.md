# Pen 图标制作指南

## 快速方案

### 方案1: 使用在线工具制作图标

1. **Favicon.cc** - https://www.favicon.cc
   - 支持手绘或上传图片转换为ICO
   - 可以直接导出16x16, 32x32, 48x48多尺寸

2. **在线ICO转换** - https://convertio.co/zh/png-to-ico
   - 上传PNG图片自动转换为ICO

3. **Canva** - https://www.canva.com
   - 免费的设计工具，有许多模板

### 方案2: 使用现有图标网站

1. **Flaticon** - https://www.flaticon.com
2. **IconFinder** - https://www.iconfinder.com
3. **Icons8** - https://icons8.com
4. **IconScout** - https://iconscout.com

搜索关键词：`pen`, `notebook`, `paste`, `clipboard`, `text`

### 方案3: 暂时使用简单图标（推荐）

先发布项目，后续再找完美图标。使用文字图标作为临时方案。

## 使用图标打包

一旦有了 `icon.ico` 文件，修改打包命令：

```bash
pyinstaller --onefile --name pen --icon icon.ico pen.py
```

## 推荐的设计风格

- 简约现代风格
- 主色调：蓝色或紫色
- 包含笔、剪贴板或文字元素
- 适合放在任务栏和开始菜单中

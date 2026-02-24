---
name: wechat-publisher
description: 将 Markdown 文件发布到微信公众号草稿箱。当用户说"发布到公众号"、"推送到微信"、"上传到草稿箱"、"publish to wechat"，或者提到微信公众号文章发布时使用。输入是 Markdown 文件，自动转换为微信兼容 HTML、上传图片、调用草稿箱 API。
---

# 微信公众号发布工具

将 Markdown 文件转换并发布到微信公众号草稿箱。

## 脚本位置

`SKILL_DIR` = 本 SKILL.md 所在目录

主脚本：`${SKILL_DIR}/scripts/publish.py`

## Python 环境

依赖安装在项目根目录的 `.venv` 下，使用 `.venv/bin/python3` 调用脚本。

若 `.venv` 不存在，先初始化：
```bash
python3 -m venv .venv
.venv/bin/pip install markdown requests Pygments beautifulsoup4 -q
```

## 配置（首次使用）

配置文件按优先级查找：

1. 项目级：`.wechat-publisher/.env`（当前工作目录下）
2. 用户级：`~/.wechat-publisher/.env`

`.env` 格式：
```
WECHAT_APP_ID=wxxxxxxxxxxxxxxxxxxx
WECHAT_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**获取凭证**：[微信公众号后台](https://mp.weixin.qq.com) → 设置与开发 → 基本配置 → AppID / AppSecret

**IP 白名单**：若报 `invalid ip not in whitelist`，在后台"基本配置 → IP白名单"添加当前公网 IP。

若无配置文件，引导用户创建：
```bash
mkdir -p .wechat-publisher
echo "WECHAT_APP_ID=\nWECHAT_APP_SECRET=" > .wechat-publisher/.env
```

## Markdown 元数据（frontmatter）

脚本支持从 frontmatter 读取元数据：

```yaml
---
title: 文章标题
author: 作者名
digest: 文章摘要（不填则自动截取首段）
cover: ./images/cover.png   # 本地路径或 https:// URL
---
```

若无 frontmatter，标题从第一个 H1 提取，其余字段留空或自动生成。

## 发布流程

```
- [ ] Step 1: 检查依赖与配置
- [ ] Step 2: 确认元数据（标题、封面图）
- [ ] Step 3: 执行发布脚本
- [ ] Step 4: 告知用户前往草稿箱确认
```

### Step 1：检查依赖与配置

若 `.venv` 不存在则自动创建并安装依赖：

```bash
if [ ! -f .venv/bin/python3 ]; then
  python3 -m venv .venv
  .venv/bin/pip install markdown requests Pygments beautifulsoup4 -q
fi
```

验证依赖：
```bash
.venv/bin/python3 -c "import markdown, requests, pygments, bs4; print('依赖 OK')"
```

检查配置：
```bash
test -f .wechat-publisher/.env && cat .wechat-publisher/.env || \
test -f ~/.wechat-publisher/.env && cat ~/.wechat-publisher/.env || \
echo "未找到配置文件"
```

### Step 2：确认元数据

| 字段 | 来源优先级 | 限制 |
|------|-----------|------|
| title | frontmatter → H1 标题 → 文件名 | ≤64字节（约21个中文字） |
| author | frontmatter → 用户输入 → 留空 | ≤8字节 |
| digest | frontmatter → 自动截取首段 | ≤120字节 |
| cover | frontmatter → 文章首图 → 无 | 建议提供，否则微信会用默认封面 |

### Step 3：执行发布脚本

```bash
# 最简用法
.venv/bin/python3 ${SKILL_DIR}/scripts/publish.py article.md

# 指定封面图（本地文件或 URL）
.venv/bin/python3 ${SKILL_DIR}/scripts/publish.py article.md --cover images/cover.png

# 指定作者
.venv/bin/python3 ${SKILL_DIR}/scripts/publish.py article.md --author "张三"

# 预览转换后的 HTML（不发布）
.venv/bin/python3 ${SKILL_DIR}/scripts/publish.py article.md --dry-run
```

成功输出示例：
```
✅ 已发布到草稿箱！
   media_id: xxx
```

### Step 4：告知用户

发布成功后告知：前往 [草稿箱](https://mp.weixin.qq.com) → 内容管理 → 草稿箱，预览效果后手动发布。

## 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `invalid ip not in whitelist` | IP 未加白名单 | 后台添加公网 IP |
| `AppSecret error` | 凭证填错 | 检查 `.env` 文件 |
| `title size out of limit` | 标题过长 | 缩短标题至 21 个中文字以内 |
| `thumb_media_id is invalid` | 封面图上传失败 | 检查图片路径/URL 是否可访问 |
| `Missing dependencies` | Python 包未安装 | `pip install markdown requests Pygments beautifulsoup4` |

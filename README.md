# 文章仓库

个人技术写作仓库，主要发布至微信公众号，同时部署为静态博客。

- **博客地址**：https://yangjiankun.com

## 定位

- **读者**：普通技术爱好者——对技术感兴趣，但不一定有专业背景
- **内容范围**：泛科技、AI 为主。涵盖 AI/LLM 趋势、产品分析、行业观察、技术科普
- **AI 的角色**：主笔。AI 独立研究并完成全文写作，用户负责审核和最终决策

## 目录结构

内容按系列组织，每个目录都有一个系列子目录层级：

```
drafts/
  popularization-of-AI/        ← AI 知识科普系列（进行中的草稿）
  build-your-agent/            ← 从零构建 AI Agent 系列（进行中的草稿）
  ai-agent-in-action/          ← 如何用 AI Agent 做事系列（进行中的草稿）
  understanding-comfyui/       ← 从零理解 ComfyUI 系列（进行中的草稿）

posts/
  popularization-of-AI/        ← AI 知识科普系列（已发布）
    01-ai-evolution-2022-2026.md
    02-llm-basics.md
    ...
  build-your-agent/            ← 从零构建 AI Agent 系列（已发布）
    01-concept.md
    02-chatbot.md
    ...
  ai-agent-in-action/          ← 如何用 AI Agent 做事系列（已发布）
    01-intro.md
    02-party-building-report.md
    ...
  ai-insights/                 ← AI Insights 系列（已发布）
    01-general-agent-eats-vertical.md
  understanding-comfyui/       ← 从零理解 ComfyUI 系列（已发布）
    01-why-comfyui-matters.md
    02-first-principles-of-image-generation.md

assets/
  popularization-of-AI/        ← AI 知识科普系列图片
    01-ai-evolution/
    02-llm-basics/
    ...
  build-your-agent/            ← 从零构建 AI Agent 系列图片
    01-concept/
    02-chatbot/
    ...
  ai-agent-in-action/          ← 如何用 AI Agent 做事系列图片
    01-intro/
    02-party-building-report/
    ...
  understanding-comfyui/       ← 从零理解 ComfyUI 系列图片
    01-why-comfyui-matters/
    02-first-principles-of-image-generation/

.vitepress/                    ← VitePress 站点配置与自定义主题
  config.mts
  theme/

.github/workflows/deploy.yml  ← GitHub Actions 自动部署到 Pages
```

- `drafts/<series>/` — 进行中的草稿。定稿发布后移至 `posts/<series>/`，草稿即可删除
- `posts/<series>/` — 已发布文章（Markdown）。视为不可变记录，发布后避免修改
- `assets/<series>/<article-slug>/` — 文章图片，按系列和文章 slug 双层组织，slug 与对应文章文件名一致
- `skills/` — Claude Code 技能
  - `write-draft`：交互式写作助手，从选题调研到完成初稿的全流程
  - `publish-draft`：将 Markdown 发布到微信公众号草稿箱

### 文件命名约定

**系列内文章必须带两位序号前缀**，格式为 `<NN>-<slug>.md`，序号从 `01` 开始：

```
posts/popularization-of-AI/01-ai-evolution-2022-2026.md
posts/popularization-of-AI/02-llm-basics.md
posts/build-your-agent/01-concept.md
posts/build-your-agent/02-chatbot.md
```

- 对应的 assets 目录名与文章 slug（含序号）保持一致：`assets/popularization-of-AI/02-llm-basics/`

### 图片路径约定

文章中图片引用使用相对路径，从文章位置出发到仓库根再进入 assets：

```markdown
<!-- 文章位于 posts/build-your-agent/01-concept.md -->
![描述](../../assets/build-your-agent/01-concept/image.png)

<!-- 文章位于 posts/popularization-of-AI/02-llm-basics.md -->
![描述](../../assets/popularization-of-AI/02-llm-basics/image.png)
```

### Mermaid 图表生成

配置文件统一使用 `assets/mermaid.config.json`（dark theme）。生成命令：

```bash
mmdc \
  -i assets/<series>/<slug>/diagram.mmd \
  -o assets/<series>/<slug>/diagram.png \
  -c assets/mermaid.config.json \
  -w 900
```

### 已有系列

| 系列目录 | 名称 | 状态 |
|---|---|---|
| `popularization-of-AI` | AI 知识科普 | 连载中 |
| `build-your-agent` | 从零构建 AI Agent | 连载中 |
| `ai-agent-in-action` | 如何用 AI Agent 做事 | 连载中 |
| `ai-insights` | AI Insights | 连载中 |
| `understanding-comfyui` | 从零理解 ComfyUI | 连载中 |

## 写作

- `/write-draft` — 写文章。包含写作风格、文章结构、质量清单等完整指南，通过交互式流程完成从选题到初稿
- `/publish-draft` — 发布文章。将 `drafts/` 中的 Markdown 发布到微信公众号草稿箱，发布后自动移至 `posts/`

## 站点开发

博客使用 VitePress 构建，部署到 GitHub Pages。

```bash
npm install          # 安装依赖
npm run docs:dev     # 本地开发
npm run docs:build   # 构建
npm run docs:preview # 预览构建产物
```

- VitePress 配置：`.vitepress/config.mts`（`srcDir: 'posts'`）
- 自定义主题：`.vitepress/theme/`（首页博客布局、系列筛选）
- 自定义域名：`yangjiankun.com`
- 推送到 main 自动触发 GitHub Actions 部署

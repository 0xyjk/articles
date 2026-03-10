---
title: 30 行代码，chatbot 变 agent
cover: ../../assets/build-your-agent/02-tool-calling/cover.png
---

# 30 行代码，chatbot 变 agent

---

你的 chatbot 现在能说话了。

你问它"帮我看看桌面上有哪些图片和视频"，它会告诉你用文件管理器怎么筛选、怎么排序。你照着做，一步一步点过去。它是顾问，你是执行者。

agent 不一样。你说"帮我看看"，它直接跑命令——列出文件、过滤出图片和视频。你说"分类放好"，它建文件夹、移文件、最后告诉你结果。整个过程在界面里逐步展开，每一条命令、每一行输出，你都能看到。

这篇文章就做这件事。

---

## Shell 是什么

**Shell**（也叫终端、命令行）是操作系统的文字界面。你平时点文件管理器来看文件、把文件拖进文件夹——shell 做的是完全一样的事，只是换成文字命令。

演示里出现的几类命令，翻译成人话：

| 命令 | 相当于用鼠标做 |
|---|---|
| `ls -lah ~/Desktop` | 打开文件管理器，查看桌面所有文件的详细信息 |
| `find ~/Desktop -iname "*.png" -o -iname "*.mov" ...` | 在桌面筛选出所有图片和视频文件 |
| `mkdir -p ~/Desktop/图片 ~/Desktop/视频` | 新建"图片"和"视频"两个文件夹 |
| `mv ~/Desktop/*.png ~/Desktop/图片/` | 把图片移进图片文件夹 |

Shell 之所以是 AI 最好用的"第一个工具"，是因为它几乎什么都能做——移文件、搜索内容、安装软件、运行程序。一个工具，覆盖本地大多数操作。

---

## 先看结果

在跟着改代码之前，先看这个东西能做什么。

这是一段两轮对话——第一轮查看，第二轮整理：

**第一轮**，输入：

> 帮我查看我桌面上的图片和视频

AI 没有只跑一个 `ls`，而是用了 `find` 加文件类型过滤，精确找出所有图片和视频文件——它自己判断出"查看"意味着要列清楚，不是随便看看。

**第二轮**，输入：

> 帮我将他们分门别类放在文件夹中

AI 创建了`图片`和`视频`两个文件夹——用中文命名，因为你说的是中文。然后用一条命令把对应格式的文件全部移了进去。

<video src="../../assets/build-your-agent/02-tool-calling/demo.mp4" controls></video>

有几件事值得注意：AI 没有被告知该建什么名字的文件夹，它自己推断出来的。它也没有被告知图片是 `.png`、`.jpg`，视频是 `.mov`、`.mp4`——这些都是它根据"图片和视频"这几个字决定的。这是 agent 和脚本的根本区别：脚本只执行你写死的逻辑，agent 能理解意图、自己决定怎么做。

文件已经在那里了，不是说说而已。

---

## AI 是怎么"用工具"的

看完演示，一个自然的问题是：AI 自己跑了那些命令？

没有。模型本身没有执行权限——它只能输出文字。Tool calling 的实际机制是：**AI 输出一张结构化的"便条"，你的代码读便条、真正执行操作、把结果还给 AI。**

便条的格式是 JSON——一种人和程序都能看懂的文字格式，长这样：`{ "key": "value" }`。

整理文件那个例子，实际发生的事是：

1. 你发"帮我查看桌面上的图片和视频"
2. 模型决定先列出文件，输出便条：`{ "tool": "shell", "command": "find ~/Desktop -iname '*.png' -o -iname '*.mov' ..." }`
3. 你的代码读到便条，执行命令，拿到文件列表
4. 文件列表塞回消息，发给模型
5. 模型看到结果，输出文字回复，告诉你找到了哪些文件
6. 你再发"帮我分门别类放好"
7. 模型输出新便条：`{ "tool": "shell", "command": "mkdir -p ~/Desktop/图片 ~/Desktop/视频 && mv ..." }`
8. 执行，完成

这个"判断 → 执行 → 看结果 → 再判断"的循环，就是 agent 和 chatbot 的本质区别。Chatbot 只说一次话。Agent 会循环——每一步根据上一步的结果来决定下一步怎么做。

`ToolLoopAgent` 名字里的 loop，就是这个意思。

### ToolLoopAgent 在做什么

揭开里面的机制，其实出乎意料地朴素：**它只是在不断往消息列表里追加内容，然后重新发给模型。**

模型每次收到的不是"这一轮的问题"，而是整个对话历史——包括它之前说的每一句话、每一张便条、每一条工具返回的结果。它"记得"自己做过什么，不是因为有什么记忆系统，而是因为那些内容就在消息列表里，它每次都能读到。

还是整理文件的例子。消息列表是怎么一步步长大的：

```
第 0 轮，发给模型：
[用户: "帮我查看桌面上的图片和视频"]

第 1 轮，发给模型：
[用户: "帮我查看桌面上的图片和视频"]
[AI便条: 执行 find ~/Desktop -iname "*.png" -o -iname "*.mov" ...]
[工具结果: 截屏A.png, 截屏B.png, 录屏C.mov ...]

第 2 轮（用户说"帮我分类放好"后），发给模型：
[用户: "帮我查看桌面上的图片和视频"]
[AI便条: 执行 find ...]
[工具结果: 截屏A.png ...]
[AI: "找到了 X 张图片、Y 个视频"]
[用户: "帮我将他们分门别类放在文件夹中"]
[AI便条: 执行 mkdir -p ~/Desktop/图片 ~/Desktop/视频 && mv ...]
[工具结果: 成功]

最终，模型看到完整历史，输出文字回复："已完成，图片移入图片文件夹，视频移入视频文件夹。"
```

`ToolLoopAgent` 帮你自动化了这个拼接过程——每次工具执行完，把便条和结果追加进列表，再调用一次模型，看看还要不要继续。直到模型决定停下来，或者达到 20 步上限。

没有这个东西，你要自己写这个 while 循环，手动维护消息列表。有了它，`createAgentUIStreamResponse` 一行搞定。

---

## 改了什么

代码变化很小，值得先说清楚，不然后面改起来心里没底。

**总共 3 处改动**：

1. 新增文件 `src/main/tools/shell.ts`（约 40 行）
2. 修改 `src/main/server.ts`：把 `streamText` 换成 `ToolLoopAgent` + `createAgentUIStreamResponse`
3. 修改 `src/renderer/src/components/ChatWindow.tsx`：加了 Terminal 组件来渲染工具调用过程

然后 `package.json` 多一个 `zod` 依赖，如果你第 1 篇已经装了就不用管。

对照篇 0 说的概念：

- `tool()` + Zod schema = 那张"便条格式定义"——告诉模型这个工具叫什么、接受什么参数
- `ToolLoopAgent` = 那个 while 循环——内置最多 20 步，不用自己管终止条件
- `createAgentUIStreamResponse` = 自动处理消息格式转换，不用手动拼工具结果进消息列表
- Terminal 组件 = 把每一步工具调用可视化，让你能看到 AI 在做什么

---

## 怎么改

以下每步的完整提示词都在 [docs/chapters/ch2-tool-calling.md](https://github.com/0xyjk/desktop-agent-template/blob/main/docs/chapters/ch2-tool-calling.md)，用 Claude Code 或 Cursor 的话直接粘贴即可。

### 第 0 步：切到第 2 篇的代码

仓库用 tag 标记了每篇对应的代码状态，直接 checkout：

```bash
git checkout ch2
pnpm install
```

> `git checkout ch2` 是把代码切换到第 2 篇对应的版本。

不想 checkout 的话，跟着下面手动改也完全可以。

### 第 1 步：装 zod

```bash
pnpm add zod
```

### 第 2 步：创建 shell 工具

新建文件 `src/main/tools/shell.ts`。

手动写的话，代码长这样：

```typescript
import { tool } from 'ai'
import { z } from 'zod'
import { execFile } from 'child_process'

function getShellConfig(): { shell: string; flag: string } {
  if (process.platform === 'win32') {
    return { shell: 'powershell.exe', flag: '-Command' }
  }
  return { shell: process.env.SHELL || '/bin/bash', flag: '-lc' }
}

function executeCommand(command: string): Promise<{ stdout: string; stderr: string }> {
  const { shell, flag } = getShellConfig()
  const finalCommand =
    process.platform === 'win32'
      ? `[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; ${command}`
      : command

  return new Promise((resolve) => {
    execFile(shell, [flag, finalCommand], { timeout: 30_000 }, (error, stdout, stderr) => {
      resolve({
        stdout: stdout.slice(0, 5000),
        stderr: error ? (stderr || error.message).slice(0, 2000) : stderr.slice(0, 2000)
      })
    })
  })
}

export const shellTool = tool({
  description: "Execute a shell command on the user's system.",
  inputSchema: z.object({
    command: z.string().describe('The shell command to execute')
  }),
  execute: async ({ command }) => {
    return await executeCommand(command)
  }
})
```

`tool()` 接受三个东西：description 告诉模型这个工具干什么，inputSchema 定义参数格式，execute 是真正执行的函数。模型看到 description 决定要不要用这个工具，看到 schema 决定怎么填参数——这就是篇 0 说的"便条格式定义"在代码里的样子。

### 第 3 步：修改 server.ts

原来的 `server.ts` 用的是 `streamText`，现在换成 `ToolLoopAgent`。

改完的 `server.ts` 完整内容：

```typescript
import { config } from 'dotenv'
config()
import { Hono } from 'hono'
import { cors } from 'hono/cors'
import { serve } from '@hono/node-server'
import { ToolLoopAgent, createAgentUIStreamResponse, UIMessage } from 'ai'
import { createOpenAICompatible } from '@ai-sdk/openai-compatible'
import { shellTool } from './tools/shell'

const provider = createOpenAICompatible({
  name: 'custom',
  apiKey: process.env.LLM_API_KEY || '',
  baseURL: process.env.LLM_BASE_URL || 'https://api.openai.com/v1'
})

const agent = new ToolLoopAgent({
  model: provider(process.env.LLM_MODEL || ''),
  tools: { shell: shellTool }
})

const app = new Hono()
app.use('/api/*', cors())

app.post('/api/chat', async (c) => {
  const { messages }: { messages: UIMessage[] } = await c.req.json()
  return createAgentUIStreamResponse({ agent, uiMessages: messages })
})

export function startServer(port = 3315): Promise<number> {
  return new Promise((resolve) => {
    serve({ fetch: app.fetch, port }, (info) => {
      resolve(info.port)
    })
  })
}
```

关键变化是 `ToolLoopAgent`。它内部实现了那个 while 循环——调用模型、执行工具、把结果追加进消息列表、再调用模型——一直循环到模型决定停止，或者达到 20 步上限。你不需要自己管这个。

### 第 4 步：修改 ChatWindow.tsx

这步是让界面能展示工具调用过程。原来只渲染文本，现在要处理 tool part——也就是每一次工具调用产生的界面块。

这步改动稍微多一点，但逻辑是直的：对每个 part 的类型做判断，文本就渲文本，工具调用就渲 Terminal 组件。

### 第 5 步：重启

```bash
pnpm dev
```

---

## 验收时刻

打开应用，先输入：

> 帮我查看我桌面上的图片和视频

它会列出找到的文件。然后再发：

> 帮我将他们分门别类放在文件夹中

试之前确保桌面上有几张截图或录屏——随手 Command+Shift+3 截几张、或者 Command+Shift+5 录一段都行。

然后看它动起来。每一步命令在 Terminal 组件里出现，有命令、有输出、有状态徽章。最后 AI 给你一段文字说明做了什么。

桌面上的截图真的进了 Screenshots 文件夹——不是模拟的。

---

## 一个必须说的事

shell 工具能执行任意命令。`rm -rf`、清空文件夹、改权限——模型说什么，它就跑什么。

在自己的开发机上玩没问题，这就是它有用的地方。但要清楚一件事：如果你让 AI 去整理文件，它可能会用你没预料到的方式——比如直接 `rm` 掉它认为是重复的文件，而不是先问你。

不是说不能用，而是要有意识地知道自己在给 AI 什么权限。对于操作重要文件或系统配置的任务，加一个确认步骤是值得的——后面的篇章会讲怎么做 human-in-the-loop。

目前，对一台你随时能恢复的机器，直接用完全没问题。

---

## 下一步

现在 agent 能执行 shell 命令了。这一个工具覆盖了本地大部分操作。

但工具只有一个。每加一个新能力，都要写一个新工具，自己维护 schema、自己更新服务器——如果你想让它能搜索网页、查日历、操作数据库，工具列表会越来越长。

下一篇讲 MCP（Model Context Protocol）——Anthropic 推出的一个开放协议。装一个 MCP server，几行配置，就能接入一整套工具；社区已经有几百个 MCP server 可用，从 GitHub 到 Google Drive 到 Slack。

一个协议，接入所有外部服务。

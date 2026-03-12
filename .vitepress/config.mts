import { defineConfig } from 'vitepress'
import { fileURLToPath } from 'node:url'

export default defineConfig({
  srcDir: 'posts',
  base: '/',

  vite: {
    server: {
      fs: {
        allow: [fileURLToPath(new URL('..', import.meta.url))],
      },
    },
  },

  title: "JK's Blog",
  description: '泛科技、AI 为主的技术写作',
  lang: 'zh-CN',

  lastUpdated: true,

  themeConfig: {
    nav: [],

    sidebar: {
      '/popularization-of-AI/': [
        {
          text: 'AI 知识科普',
          items: [
            { text: 'AI进化史：从ChatGPT到Agent时代', link: '/popularization-of-AI/01-ai-evolution-2022-2026' },
            { text: 'AI 是怎么学会说话的', link: '/popularization-of-AI/02-llm-basics' },
            { text: 'AI 是怎么学会思考的', link: '/popularization-of-AI/03-ai-reasoning' },
            { text: 'AI 是怎么学会"看"和"听"的', link: '/popularization-of-AI/04-multimodal-ai' },
            { text: 'AI 的手脚进化史', link: '/popularization-of-AI/05-ai-tool-use-and-agent' },
            { text: 'Agent 的两条路', link: '/popularization-of-AI/06-cloud-vs-local-agent' },
          ],
        },
      ],
      '/build-your-agent/': [
        {
          text: '从零构建 AI Agent',
          items: [
            { text: '从零理解 AI Agent', link: '/build-your-agent/01-concept' },
            { text: '30 分钟搭一个桌面 AI 助手', link: '/build-your-agent/02-chatbot' },
            { text: '30 行代码，chatbot 变 agent', link: '/build-your-agent/03-tool-calling' },
            { text: '一个协议，接入所有外部服务', link: '/build-your-agent/04-mcp' },
            { text: '不写代码，扩展 agent 能力——Skill 系统', link: '/build-your-agent/05-skills' },
            { text: '代码执行：让 agent 不再靠猜', link: '/build-your-agent/06-code-executor' },
            { text: '记忆系统：让 agent 记住你是谁', link: '/build-your-agent/07-memory' },
          ],
        },
      ],
      '/ai-agent-in-action/': [
        {
          text: 'AI Agent 实战',
          items: [
            { text: '工具选好，事才好做——系列开篇', link: '/ai-agent-in-action/01-intro' },
            { text: '用 AI Agent 写每月材料', link: '/ai-agent-in-action/02-party-building-report' },
            { text: '用 Remotion 做教学视频', link: '/ai-agent-in-action/03-teaching-video-with-remotion' },
            { text: '用 AI Agent 写公众号：从构思到发布', link: '/ai-agent-in-action/04-wechat-writing-workflow' },
          ],
        },
      ],
      '/ai-insights/': [
        {
          text: 'AI Insights',
          items: [
            { text: '通用 Agent 终将吃掉垂类 Agent', link: '/ai-insights/01-general-agent-eats-vertical' },
          ],
        },
      ],
    },

    socialLinks: [],

    outline: {
      level: [2, 3],
      label: '目录',
    },

    lastUpdated: {
      text: '最后更新',
    },

    docFooter: {
      prev: '上一篇',
      next: '下一篇',
    },

    darkModeSwitchLabel: '主题',
    sidebarMenuLabel: '菜单',
    returnToTopLabel: '回到顶部',
  },
})

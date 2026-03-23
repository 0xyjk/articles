import { defineConfig } from 'vitepress'
import { fileURLToPath } from 'node:url'
import { buildSidebar } from './series'

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

    sidebar: buildSidebar(),

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

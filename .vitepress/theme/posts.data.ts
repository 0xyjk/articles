import { createContentLoader } from 'vitepress'

interface Post {
  title: string
  url: string
  index: string
}

interface SeriesGroup {
  name: string
  description: string
  prefix: string
  posts: Post[]
}

const seriesConfig = [
  {
    name: 'AI 知识科普',
    description: '从 ChatGPT 到 Agent 时代，用通俗语言解读 AI 的核心概念',
    prefix: '/popularization-of-AI/',
  },
  {
    name: '从零构建 AI Agent',
    description: '手把手教你搭建自己的 AI Agent，从概念到实现',
    prefix: '/build-your-agent/',
  },
  {
    name: 'AI Agent 实战',
    description: '真实场景下用 AI Agent 做事的经验分享',
    prefix: '/ai-agent-in-action/',
  },
]

export default createContentLoader('**/*.md', {
  transform(rawData): SeriesGroup[] {
    return seriesConfig.map(({ name, description, prefix }) => ({
      name,
      description,
      prefix,
      posts: rawData
        .filter((p) => p.url.startsWith(prefix) && !p.url.endsWith('/'))
        .sort((a, b) => a.url.localeCompare(b.url))
        .map((p) => {
          const match = p.url.match(/\/(\d+)-/)
          return {
            title: p.frontmatter.title || '',
            url: p.url,
            index: match ? String(Number(match[1]) + 1).padStart(2, '0') : '',
          }
        }),
    }))
  },
})

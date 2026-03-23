import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export interface SeriesMeta {
  key: string
  name: string
  description: string
  prefix: string
}

export const seriesConfig: SeriesMeta[] = [
  {
    key: 'popularization-of-AI',
    name: 'AI 知识科普',
    description: '从 ChatGPT 到 Agent 时代，用通俗语言解读 AI 的核心概念',
    prefix: '/popularization-of-AI/',
  },
  {
    key: 'build-your-agent',
    name: '从零构建 AI Agent',
    description: '手把手教你搭建自己的 AI Agent，从概念到实现',
    prefix: '/build-your-agent/',
  },
  {
    key: 'ai-agent-in-action',
    name: 'AI Agent 实战',
    description: '真实场景下用 AI Agent 做事的经验分享',
    prefix: '/ai-agent-in-action/',
  },
  {
    key: 'ai-insights',
    name: 'AI Insights',
    description: '个人对 AI 行业趋势的思考与判断',
    prefix: '/ai-insights/',
  },
  {
    key: 'understanding-comfyui',
    name: '从零理解 ComfyUI',
    description: '从工作流视角理解图片和视频生成的底层原理',
    prefix: '/understanding-comfyui/',
  },
]

function stripQuotes(value: string) {
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    return value.slice(1, -1)
  }

  return value
}

function readTitle(filePath: string) {
  const content = fs.readFileSync(filePath, 'utf8')
  const frontmatter = content.match(/^---\n([\s\S]*?)\n---/)

  if (!frontmatter) {
    return path.basename(filePath, '.md')
  }

  const titleLine = frontmatter[1]
    .split('\n')
    .find((line) => line.startsWith('title:'))

  if (!titleLine) {
    return path.basename(filePath, '.md')
  }

  return stripQuotes(titleLine.slice('title:'.length).trim())
}

export function buildSidebar() {
  const postsRoot = fileURLToPath(new URL('../posts', import.meta.url))

  return Object.fromEntries(
    seriesConfig.flatMap(({ key, name, prefix }) => {
      const seriesDir = path.join(postsRoot, key)

      if (!fs.existsSync(seriesDir)) {
        return []
      }

      const items = fs
        .readdirSync(seriesDir)
        .filter((entry) => entry.endsWith('.md'))
        .sort((a, b) => a.localeCompare(b))
        .map((entry) => {
          const filePath = path.join(seriesDir, entry)

          return {
            text: readTitle(filePath),
            link: `/${key}/${entry.replace(/\.md$/, '')}`,
          }
        })

      if (!items.length) {
        return []
      }

      return [[prefix, [{ text: name, items }]]]
    }),
  )
}

import { createContentLoader } from 'vitepress'
import { seriesConfig } from '../series'

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

export default createContentLoader('**/*.md', {
  transform(rawData): SeriesGroup[] {
    return seriesConfig
      .map(({ name, description, prefix }) => ({
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
              index: match ? String(Number(match[1])).padStart(2, '0') : '',
            }
          }),
      }))
      .filter((group) => group.posts.length > 0)
  },
})

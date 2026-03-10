<script setup lang="ts">
import { ref, computed } from 'vue'
import { data as series } from './posts.data'
import { withBase } from 'vitepress'

const activeFilter = ref<string | null>(null)

function toggle(name: string) {
  activeFilter.value = activeFilter.value === name ? null : name
}

const filtered = computed(() =>
  activeFilter.value
    ? series.filter((g) => g.name === activeFilter.value)
    : series,
)
</script>

<template>
  <div class="blog-home">
    <div class="filter-bar">
      <button
        v-for="group in series"
        :key="group.name"
        class="filter-tag"
        :class="{ active: activeFilter === group.name }"
        @click="toggle(group.name)"
      >
        {{ group.name }}
        <span class="tag-count">{{ group.posts.length }}</span>
      </button>
    </div>

    <section v-for="group in filtered" :key="group.name" class="series">
      <a :href="withBase(group.posts[0]?.url)" class="series-card">
        <div class="series-info">
          <h2 class="series-name">{{ group.name }}</h2>
          <p class="series-desc">{{ group.description }}</p>
        </div>
        <span class="series-arrow">&rarr;</span>
      </a>
      <div class="post-list">
        <a
          v-for="post in group.posts"
          :key="post.url"
          :href="withBase(post.url)"
          class="post-row"
        >
          <span class="post-index">{{ post.index }}</span>
          <span class="post-title">{{ post.title }}</span>
          <span class="post-arrow">&rsaquo;</span>
        </a>
      </div>
    </section>
  </div>
</template>

<style scoped>
.blog-home {
  max-width: 720px;
  margin: 0 auto;
  padding: 56px 24px 80px;
}

/* --- Filter tags --- */
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 40px;
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1px solid var(--vp-c-divider);
  border-radius: 99px;
  background: transparent;
  color: var(--vp-c-text-2);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-tag:hover {
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-brand-1);
}

.filter-tag.active {
  background: var(--vp-c-brand-1);
  border-color: var(--vp-c-brand-1);
  color: var(--vp-c-white);
}

.filter-tag.active .tag-count {
  background: rgba(255, 255, 255, 0.25);
  color: var(--vp-c-white);
}

.tag-count {
  font-size: 0.7rem;
  font-weight: 600;
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-3);
  padding: 1px 7px;
  border-radius: 99px;
  transition: all 0.2s;
}

/* --- Series card --- */
.series {
  margin-bottom: 48px;
}

.series:last-child {
  margin-bottom: 0;
}

.series-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 28px;
  border-radius: 12px;
  background: var(--vp-c-bg-soft);
  text-decoration: none;
  transition: background-color 0.2s;
  margin-bottom: 4px;
}

.series-card:hover {
  background: var(--vp-c-bg-elv);
}

.series-info {
  flex: 1;
}

.series-name {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--vp-c-text-1);
  margin: 0 0 6px;
  line-height: 1.3;
}

.series-desc {
  font-size: 0.85rem;
  color: var(--vp-c-text-3);
  margin: 0;
  line-height: 1.5;
}

.series-arrow {
  font-size: 1.5rem;
  color: var(--vp-c-text-3);
  margin-left: 16px;
  flex-shrink: 0;
}

.series-card:hover .series-arrow {
  color: var(--vp-c-brand-1);
}

/* --- Post rows --- */
.post-list {
  display: flex;
  flex-direction: column;
}

.post-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 28px;
  text-decoration: none;
  border-radius: 8px;
  transition: background-color 0.15s;
}

.post-row:hover {
  background: var(--vp-c-bg-soft);
}

.post-index {
  flex-shrink: 0;
  font-size: 0.75rem;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
  color: var(--vp-c-text-3);
  width: 22px;
  text-align: right;
}

.post-title {
  flex: 1;
  font-size: 0.9rem;
  color: var(--vp-c-text-2);
  line-height: 1.4;
}

.post-row:hover .post-title {
  color: var(--vp-c-text-1);
}

.post-arrow {
  flex-shrink: 0;
  font-size: 1.1rem;
  color: var(--vp-c-text-3);
  opacity: 0;
  transition: opacity 0.15s;
}

.post-row:hover .post-arrow {
  opacity: 1;
  color: var(--vp-c-brand-1);
}

/* --- Responsive --- */
@media (max-width: 640px) {
  .blog-home {
    padding: 32px 16px 60px;
  }

  .series-card {
    padding: 20px 20px;
  }

  .post-row {
    padding: 10px 20px;
  }
}
</style>

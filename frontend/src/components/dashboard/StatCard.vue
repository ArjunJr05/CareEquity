<script setup>
import { computed } from 'vue'
import IconBase from './IconBase.vue'

const props = defineProps({
  icon: { type: String, required: true },
  tone: { type: String, default: 'blue' },
  label: { type: String, required: true },
  value: { type: String, required: true },
  trend: { type: String, required: true },
  trendUp: { type: Boolean, default: true },
  trendIcon: { type: String, default: '' },
  showTrendIcon: { type: Boolean, default: true },
  caption: { type: String, default: 'vs last 30 days' },
  spark: { type: Array, default: () => [0.3, 0.4, 0.35, 0.5, 0.45, 0.6, 0.7] },
})

const points = computed(() =>
  props.spark
    .map((v, i) => `${(i / (props.spark.length - 1)) * 100},${30 - v * 26}`)
    .join(' '),
)

const strokeColor = computed(() => {
  if (props.tone === 'blue') return 'var(--brand)'
  if (props.tone === 'red') return 'var(--red)'
  if (props.tone === 'purple') return 'var(--purple)'
  if (props.tone === 'teal') return 'var(--teal)'
  if (props.tone === 'indigo') return 'var(--indigo)'
  return 'var(--brand)'
})

const iconName = computed(() => {
  if (props.trendIcon) return props.trendIcon
  return props.trendUp ? 'arrow-up' : 'arrow-down'
})
</script>

<template>
  <article class="stat-card">
    <div class="stat-top">
      <span class="stat-icon" :class="tone"><IconBase :name="icon" :size="17" /></span>
      <span class="stat-label">{{ label }}</span>
    </div>

    <div class="stat-value">{{ value }}</div>

    <div class="stat-bottom">
      <span class="stat-trend" :class="[trendUp ? 'up' : 'down', tone]">
        <IconBase v-if="showTrendIcon" :name="iconName" :size="11" />
        {{ trend }}
      </span>
      <span class="stat-caption">{{ caption }}</span>
    </div>

    <svg class="spark" viewBox="0 0 100 30" preserveAspectRatio="none">
      <polyline
        :points="points"
        fill="none"
        :stroke="strokeColor"
        stroke-width="2.2"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
  </article>
</template>

<style scoped>
.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 18px;
  box-shadow: var(--shadow-sm);
  position: relative;
  overflow: hidden;
}

.stat-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.stat-icon {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon.blue {
  background: var(--brand-light);
  color: var(--brand);
}
.stat-icon.red {
  background: var(--red-bg);
  color: var(--red);
}
.stat-icon.purple {
  background: var(--purple-bg);
  color: var(--purple);
}
.stat-icon.teal {
  background: var(--teal-bg);
  color: var(--teal);
}
.stat-icon.indigo {
  background: var(--indigo-bg);
  color: var(--indigo);
}

.stat-label {
  font-size: 0.82rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.stat-value {
  font-size: 1.9rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
  margin-bottom: 10px;
}

.stat-bottom {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.stat-trend {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 0.76rem;
  font-weight: 700;
}

.stat-trend.up {
  color: var(--teal);
}
.stat-trend.down {
  color: var(--red);
}
.stat-trend.red {
  color: var(--red-text);
}
.stat-trend.purple {
  color: var(--purple);
}
.stat-trend.teal {
  color: var(--teal);
}
.stat-trend.blue {
  color: var(--brand);
}
.stat-trend.indigo {
  color: var(--indigo);
}

.stat-caption {
  font-size: 0.72rem;
  color: var(--text-tertiary);
}

.spark {
  width: 100%;
  height: 28px;
  display: block;
}
</style>

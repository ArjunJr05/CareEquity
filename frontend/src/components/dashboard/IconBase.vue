<script setup>
defineProps({
  name: { type: String, required: true },
  size: { type: Number, default: 20 },
})
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.8"
    stroke-linecap="round"
    stroke-linejoin="round"
    class="icon"
  >
    <template v-if="name === 'home'">
      <path d="M3 11.5 12 4l9 7.5" />
      <path d="M5 10v9a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1v-9" />
    </template>
    <template v-else-if="name === 'users'">
      <circle cx="9" cy="8" r="3.2" />
      <path d="M2.5 20c0-3.6 2.9-6 6.5-6s6.5 2.4 6.5 6" />
      <circle cx="17.5" cy="9" r="2.6" />
      <path d="M15.4 14.2c2.6.5 4.1 2.3 4.1 5.3" />
    </template>
    <template v-else-if="name === 'map'">
      <path d="M9 4 3 6.2v13.8l6-2.2 6 2.2 6-2.2V3.8l-6 2.2-6-2.2Z" />
      <path d="M9 4v13.8M15 6.2V20" />
    </template>
    <template v-else-if="name === 'pulse'">
      <circle cx="12" cy="12" r="9.3" />
      <path d="M6.5 12h2.2l1.6-4.2 3 8.4 1.6-4.2h2.6" />
    </template>
    <template v-else-if="name === 'trend'">
      <path d="M3 17 9.5 10l4 4L21 6" />
      <path d="M15 6h6v6" />
    </template>
    <template v-else-if="name === 'hand-heart'">
      <path
        d="M12 19.4c-2.6-1.8-7.6-5.3-7.6-9.7 0-2.4 1.9-4.2 4.2-4.2 1.5 0 2.7.7 3.4 1.8.7-1.1 1.9-1.8 3.4-1.8 2.3 0 4.2 1.8 4.2 4.2 0 4.4-5 7.9-7.6 9.7Z"
      />
    </template>
    <template v-else-if="name === 'bulb'">
      <path d="M9 18.5h6M10 21.5h4M7 10a5 5 0 1 1 10 0c0 2-1.2 3-2 4-.6.7-1 1.3-1 2H10c0-.7-.4-1.3-1-2-.8-1-2-2-2-4Z" />
    </template>
    <template v-else-if="name === 'report'">
      <rect x="5" y="3" width="14" height="18" rx="2" />
      <path d="M9 8h6M9 12h6M9 16h3" />
    </template>
    <template v-else-if="name === 'shield'">
      <path d="M12 3 5 5.5V11c0 5 3 8.5 7 10 4-1.5 7-5 7-10V5.5L12 3Z" />
      <path d="m9 12 2 2 4-4.5" />
    </template>
    <template v-else-if="name === 'search'">
      <circle cx="11" cy="11" r="6.5" />
      <path d="m20 20-4.3-4.3" />
    </template>
    <template v-else-if="name === 'pin'">
      <path d="M12 21s7-6.1 7-11.5A7 7 0 0 0 5 9.5C5 14.9 12 21 12 21Z" />
      <circle cx="12" cy="9.5" r="2.3" />
    </template>
    <template v-else-if="name === 'calendar'">
      <rect x="3.5" y="5" width="17" height="16" rx="2" />
      <path d="M3.5 9.5h17M8 3v4M16 3v4" />
    </template>
    <template v-else-if="name === 'bell'">
      <path d="M6 10a6 6 0 0 1 12 0c0 4 1.5 5.5 1.5 5.5H4.5S6 14 6 10Z" />
      <path d="M10 19a2 2 0 0 0 4 0" />
    </template>
    <template v-else-if="name === 'chevron-right'">
      <path d="m9 5 7 7-7 7" />
    </template>
    <template v-else-if="name === 'chevron-left'">
      <path d="m15 19-7-7 7-7" />
    </template>
    <template v-else-if="name === 'chevron-down'">
      <path d="m5 8 7 7 7-7" />
    </template>
    <template v-else-if="name === 'arrow-up'">
      <path d="M12 19V5M6 11l6-6 6 6" />
    </template>
    <template v-else-if="name === 'arrow-down'">
      <path d="M12 5v14M6 13l6 6 6-6" />
    </template>
    <template v-else-if="name === 'plus'">
      <path d="M12 5v14M5 12h14" />
    </template>
    <template v-else-if="name === 'minus'">
      <path d="M5 12h14" />
    </template>
    <template v-else-if="name === 'locate'">
      <circle cx="12" cy="12" r="2.4" />
      <path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3" />
    </template>
    <template v-else-if="name === 'filter'">
      <path d="M4 5h16M7 12h10M10 19h4" />
    </template>
    <template v-else-if="name === 'close'">
      <path d="M6 6l12 12M18 6 6 18" />
    </template>
    <template v-else-if="name === 'external'">
      <path d="M14 4h6v6M20 4 10 14M6 4H5a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-1" />
    </template>
    <template v-else-if="name === 'alert'">
      <path d="M12 3 2 20h20L12 3Z" />
      <path d="M12 10v4M12 17h.01" />
    </template>
    <template v-else-if="name === 'puzzle'">
      <path
        d="M9 4h4v2.1a1.9 1.9 0 1 0 0 3.8V12h4v3.9a1.9 1.9 0 1 1 0 3.8V20H9v-3.9a1.9 1.9 0 1 0 0-3.8V9H5a1 1 0 0 1-1-1V5a1 1 0 0 1 1-1h4Z"
      />
    </template>
    <template v-else-if="name === 'sparkle'">
      <path d="M12 3v4M12 17v4M3 12h4M17 12h4" />
      <path d="m6.5 6.5 2 2M15.5 15.5l2 2M17.5 6.5l-2 2M8.5 15.5l-2 2" />
    </template>
    <template v-else-if="name === 'heart'">
      <path
        d="M12 20.2s-7.2-4.5-9.4-9C1.4 8 2.9 4.6 6 4c2.1-.4 3.7.7 6 2.9C14.3 4.7 15.9 3.6 18 4c3.1.6 4.6 4 2.4 7.2-2.2 4.5-9.4 9-9.4 9Z"
      />
    </template>
    <template v-else-if="name === 'desktop'">
      <rect x="3" y="4" width="18" height="12" rx="1.5" />
      <path d="M8 20h8M12 16v4" />
    </template>
    <template v-else-if="name === 'tablet'">
      <rect x="6" y="3" width="12" height="18" rx="1.5" />
      <path d="M11 18h2" />
    </template>
    <template v-else-if="name === 'mobile'">
      <rect x="8" y="2" width="8" height="20" rx="1.5" />
      <path d="M11 19h2" />
    </template>
    <template v-else-if="name === 'scales'">
      <path d="M9 22h6M12 2v20M12 5L5 7M12 5l7 2M5 7v6a7 7 0 0 0 14 0V7" />
    </template>
    <template v-else-if="name === 'target'">
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="6" />
      <circle cx="12" cy="12" r="2" />
    </template>
    <template v-else-if="name === 'eye'">
      <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
      <circle cx="12" cy="12" r="3" />
    </template>
    <template v-else-if="name === 'download'">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" stroke-width="2" />
    </template>
    <template v-else-if="name === 'cloud-upload'">
      <path d="M12 16V9M8 12l4-4 4 4" stroke-width="2" />
      <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3a5 5 0 0 0 6.6 2.09" stroke-width="2" />
    </template>
    <template v-else-if="name === 'help'">
      <circle cx="12" cy="12" r="10" />
      <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </template>
    <template v-else-if="name === 'lock'">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" stroke-width="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke-width="2" />
    </template>
    <template v-else-if="name === 'subscription' || name === 'credit-card' || name === 'plan'">
      <rect x="2" y="5" width="20" height="14" rx="2.5" stroke-width="1.8" />
      <line x1="2" y1="10" x2="22" y2="10" stroke-width="1.8" />
      <line x1="6" y1="15" x2="9" y2="15" stroke-width="2" />
      <line x1="12" y1="15" x2="16" y2="15" stroke-width="2" />
    </template>
    <template v-else>
      <circle cx="12" cy="12" r="9" />
    </template>
  </svg>
</template>

<style scoped>
.icon {
  flex-shrink: 0;
}
</style>

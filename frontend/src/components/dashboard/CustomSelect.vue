<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import IconBase from './IconBase.vue'

const props = defineProps({
  modelValue: [String, Number],
  options: {
    type: Array,
    default: () => []
  },
  disabled: Boolean,
  placeholder: String
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const searchQuery = ref('')
const searchInput = ref(null)

const formattedOptions = computed(() => {
  return props.options.map(opt => {
    if (typeof opt === 'object' && opt !== null) {
      return { label: opt.label || opt.value, value: opt.value }
    }
    return { label: String(opt), value: opt }
  })
})

const filteredOptions = computed(() => {
  if (!searchQuery.value.trim()) return formattedOptions.value
  const q = searchQuery.value.toLowerCase().trim()
  return formattedOptions.value.filter(o => o.label.toLowerCase().includes(q))
})

const selectedLabel = computed(() => {
  const found = formattedOptions.value.find(o => o.value === props.modelValue)
  return found ? found.label : (props.modelValue || props.placeholder || 'Select...')
})

watch(isOpen, (val) => {
  if (val) {
    searchQuery.value = ''
    if (formattedOptions.value.length > 5) {
      nextTick(() => {
        if (searchInput.value) searchInput.value.focus()
      })
    }
  }
})

function selectOption(val) {
  emit('update:modelValue', val)
  isOpen.value = false
}
</script>

<template>
  <div class="custom-select-container" :class="{ disabled }">
    <div 
      class="custom-select-trigger" 
      :class="{ open: isOpen, disabled }"
      @click="!disabled && (isOpen = !isOpen)"
    >
      <span class="trigger-label font-semibold">{{ selectedLabel }}</span>
      <IconBase name="chevron-down" :size="13" class="chevron" :class="{ rotated: isOpen }" />
    </div>

    <!-- Backdrop -->
    <div v-if="isOpen" class="custom-select-backdrop" @click="isOpen = false"></div>

    <!-- Options Menu -->
    <transition name="menu-pop">
      <div v-if="isOpen" class="custom-select-menu-wrapper">
        <div v-if="formattedOptions.length > 5" class="search-box-header" @click.stop>
          <input 
            ref="searchInput"
            v-model="searchQuery" 
            type="text" 
            placeholder="Type to filter..." 
            class="select-search-input" 
          />
        </div>

        <ul class="custom-select-menu">
          <li 
            v-for="opt in filteredOptions" 
            :key="opt.value"
            class="custom-select-option"
            :class="{ active: modelValue === opt.value }"
            @click="selectOption(opt.value)"
          >
            <span>{{ opt.label }}</span>
            <span v-if="modelValue === opt.value" class="active-check">✓</span>
          </li>
          <li v-if="filteredOptions.length === 0" class="no-options">
            No matching options
          </li>
        </ul>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.custom-select-container {
  position: relative;
  width: 100%;
  user-select: none;
}

.custom-select-trigger {
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 8px 12px;
  background: #ffffff;
  font-size: 0.78rem;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all 0.15s ease;
  height: 38px;
}

.custom-select-trigger:hover:not(.disabled) {
  border-color: #cbd5e1;
  background: #f8fafc;
}

.custom-select-trigger.open {
  border-color: var(--brand);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.custom-select-trigger.disabled {
  background: #f1f5f9;
  cursor: not-allowed;
  opacity: 0.7;
}

.trigger-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chevron {
  color: var(--text-secondary);
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.chevron.rotated {
  transform: rotate(180deg);
}

.custom-select-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 99;
}

.custom-select-menu-wrapper {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
  padding: 6px;
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.search-box-header {
  padding: 2px 2px 4px;
}

.select-search-input {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 0.75rem;
  color: var(--text-primary);
  outline: none;
  background: #f8fafc;
  box-sizing: border-box;
}

.select-search-input:focus {
  border-color: var(--brand);
  background: #ffffff;
}

.custom-select-menu {
  padding: 0;
  margin: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 3px;
  max-height: 200px;
  overflow-y: auto;
}

.custom-select-menu::-webkit-scrollbar {
  width: 5px;
}

.custom-select-menu::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.custom-select-menu::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.custom-select-menu::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.custom-select-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 0.78rem;
  color: var(--text-primary);
  cursor: pointer;
  transition: background 0.15s ease;
}

.custom-select-option:hover {
  background: #f1f5f9;
}

.custom-select-option.active {
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 700;
}

.active-check {
  color: #2563eb;
  font-weight: bold;
}

.no-options {
  padding: 12px;
  text-align: center;
  font-size: 0.75rem;
  color: #94a3b8;
  font-style: italic;
}

.menu-pop-enter-active,
.menu-pop-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.menu-pop-enter-from,
.menu-pop-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}
</style>

<template>
  <div class="flex items-center gap-1 px-5 py-2.5 border-b overflow-hidden">
    <button
      v-for="cat in categories"
      :key="cat.value"
      class="flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm transition-colors whitespace-nowrap"
      :class="
        modelValue === cat.value
          ? 'bg-surface-gray-3 text-ink-gray-9'
          : 'text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-7'
      "
      @click="$emit('update:modelValue', cat.value)"
    >
      <span>{{ __(cat.label) }}</span>
      <Badge
        :label="counts[cat.value] || 0"
        variant="subtle"
        class="text-xs"
      />
    </button>
  </div>
</template>

<script setup>
import { Badge } from 'frappe-ui'

defineProps({
  categories: { type: Array, required: true },
  counts: { type: Object, required: true },
})

const modelValue = defineModel({ type: String })
</script>

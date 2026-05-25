<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button
        :tooltip="__('Обновить')"
        :icon="RefreshIcon"
        :loading="loading"
        @click="loadPresences"
      />
    </template>
  </LayoutHeader>

  <div class="flex flex-col h-full overflow-auto px-5 py-4">
    <div v-if="loading && !presences.length" class="flex items-center justify-center h-32 text-ink-gray-4">
      {{ __('Загрузка...') }}
    </div>

    <div v-else-if="!presences.length" class="flex flex-col items-center justify-center h-full text-ink-gray-4 gap-2">
      <PresencesIcon class="w-10 h-10 opacity-30" />
      <p class="text-base">{{ __('Нет данных') }}</p>
    </div>

    <div v-else class="flex flex-col gap-3">
      <!-- Filter buttons -->
      <div class="flex gap-2 pb-1">
        <button
          class="flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all border"
          :class="activeFilter === 'all'
            ? 'bg-gray-800 text-white border-gray-800'
            : 'bg-surface-white text-ink-gray-6 border-outline-gray-2 hover:border-outline-gray-3'"
          @click="activeFilter = 'all'"
        >
          Все: {{ presences.length }}
        </button>
        <button
          class="flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all border"
          :class="activeFilter === 'В офисе'
            ? 'bg-green-600 text-white border-green-600'
            : 'bg-surface-white text-green-700 border-outline-gray-2 hover:border-green-300'"
          @click="activeFilter = 'В офисе'"
        >
          <span class="w-2 h-2 rounded-full inline-block" :class="activeFilter === 'В офисе' ? 'bg-white' : 'bg-green-500'"></span>
          {{ __('В офисе') }}: {{ inOfficeCount }}
        </button>
        <button
          class="flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all border"
          :class="activeFilter === 'Не в офисе'
            ? 'bg-gray-500 text-white border-gray-500'
            : 'bg-surface-white text-ink-gray-5 border-outline-gray-2 hover:border-outline-gray-3'"
          @click="activeFilter = 'Не в офисе'"
        >
          <span class="w-2 h-2 rounded-full inline-block" :class="activeFilter === 'Не в офисе' ? 'bg-white' : 'bg-gray-300'"></span>
          {{ __('Не в офисе') }}: {{ notInOfficeCount }}
        </button>
      </div>

      <!-- Employee list -->
      <div
        v-for="emp in filteredPresences"
        :key="emp.email"
        class="flex items-center justify-between rounded-lg border border-outline-gray-1 bg-surface-white px-4 py-3 shadow-sm"
      >
        <div class="flex items-center gap-3">
          <div class="flex h-9 w-9 items-center justify-center rounded-full bg-surface-gray-3 overflow-hidden shrink-0">
            <img
              v-if="emp.user_image"
              :src="emp.user_image"
              :alt="emp.full_name"
              class="h-full w-full object-cover"
            />
            <span v-else class="text-sm font-medium text-ink-gray-6">
              {{ initials(emp.full_name) }}
            </span>
          </div>
          <span class="text-base text-ink-gray-8">{{ emp.full_name }}</span>
        </div>
        <span
          class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
          :class="emp.status === 'В офисе'
            ? 'bg-green-50 text-green-700 ring-1 ring-inset ring-green-600/20'
            : 'bg-gray-100 text-ink-gray-5 ring-1 ring-inset ring-gray-400/20'"
        >
          {{ emp.status }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import PresencesIcon from '@/components/Icons/PresencesIcon.vue'
import RefreshIcon from '@/components/Icons/RefreshIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { Breadcrumbs, call, toast } from 'frappe-ui'
import { ref, computed, onMounted, onUnmounted } from 'vue'

const breadcrumbs = [{ label: __('Присутствия'), route: { name: 'Presences' } }]

const presences = ref([])
const loading = ref(false)
const activeFilter = ref('all')

const inOfficeCount = computed(() => presences.value.filter(e => e.status === 'В офисе').length)
const notInOfficeCount = computed(() => presences.value.filter(e => e.status !== 'В офисе').length)
const filteredPresences = computed(() => {
  if (activeFilter.value === 'all') return presences.value
  return presences.value.filter(e => e.status === activeFilter.value)
})

function initials(name) {
  if (!name) return '?'
  return name.split(' ').slice(0, 2).map(p => p[0]).join('').toUpperCase()
}

async function loadPresences() {
  loading.value = true
  try {
    presences.value = await call('crm.integrations.presence_api.get_presences')
  } catch {
    toast.error(__('Не удалось загрузить данные о присутствии'))
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadPresences()

  $socket.on('presence_updated', ({ email, status }) => {
    const emp = presences.value.find(e => e.email === email)
    if (emp) emp.status = status
    else loadPresences()
  })

  $socket.on('presences_bulk_updated', ({ statuses }) => {
    presences.value.forEach(emp => {
      if (statuses[emp.email] !== undefined) {
        emp.status = statuses[emp.email]
      }
    })
  })
})

onUnmounted(() => {
  $socket.off('presence_updated')
  $socket.off('presences_bulk_updated')
})
</script>

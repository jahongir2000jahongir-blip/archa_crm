<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button
        variant="ghost"
        icon="refresh-cw"
        :loading="loading"
        :label="__('Обновить')"
        @click="loadData"
      />
    </template>
  </LayoutHeader>

  <div class="flex flex-col h-full overflow-hidden">
    <!-- Tabs -->
    <div class="flex items-center gap-1 px-5 py-2.5 border-b overflow-x-auto">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition-colors whitespace-nowrap"
        :class="
          activeTab === tab.key
            ? 'bg-surface-gray-3 text-ink-gray-9 font-medium'
            : 'text-ink-gray-5 hover:bg-surface-gray-2 hover:text-ink-gray-7'
        "
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
        <span
          v-if="counts[tab.key]"
          class="inline-flex items-center justify-center rounded-full bg-surface-gray-4 px-1.5 text-xs text-ink-gray-7 min-w-[18px]"
        >
          {{ counts[tab.key] }}
        </span>
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex flex-1 items-center justify-center text-ink-gray-4">
      <div class="flex flex-col items-center gap-2">
        <div class="animate-spin h-6 w-6 border-2 border-outline-gray-3 border-t-ink-gray-6 rounded-full" />
        <span class="text-sm">{{ __('Загрузка...') }}</span>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex flex-1 items-center justify-center">
      <div class="text-center text-ink-red-3">
        <p class="text-base font-medium">{{ __('Ошибка загрузки данных') }}</p>
        <p class="text-sm mt-1 text-ink-gray-5">{{ error }}</p>
      </div>
    </div>

    <!-- Empty -->
    <div
      v-else-if="!currentRows.length"
      class="flex flex-1 items-center justify-center text-ink-gray-4"
    >
      <div class="flex flex-col items-center gap-2">
        <SalesIcon class="w-10 h-10 opacity-30" />
        <p class="text-sm">{{ __('Нет данных за выбранный период') }}</p>
      </div>
    </div>

    <!-- Table -->
    <div v-else class="flex-1 overflow-auto px-5 py-3">
      <!-- Summary -->
      <div class="flex gap-6 mb-4 flex-wrap">
        <div class="flex flex-col">
          <span class="text-xs text-ink-gray-5">{{ __('Итого (TJS)') }}</span>
          <span class="text-lg font-semibold text-ink-gray-9">{{ formatMoney(totalAmount) }}</span>
        </div>
        <div class="w-px bg-gray-200 self-stretch" />
        <div class="flex flex-col">
          <span class="text-xs text-ink-gray-5">{{ __('Записей') }}</span>
          <span class="text-lg font-semibold text-ink-gray-9">{{ currentRows.length }}</span>
        </div>
      </div>

      <!-- Data table -->
      <table class="w-full text-sm border-collapse">
        <thead>
          <tr class="border-b">
            <th class="text-left py-2 px-3 text-ink-gray-5 font-medium">{{ __('Магазин') }}</th>
            <th class="text-left py-2 px-3 text-ink-gray-5 font-medium">{{ __('Направление') }}</th>
            <th
              v-if="activeTab === 'plan'"
              class="text-left py-2 px-3 text-ink-gray-5 font-medium"
            >{{ __('Период') }}</th>
            <th class="text-left py-2 px-3 text-ink-gray-5 font-medium">{{ __('Менеджер') }}</th>
            <th class="text-right py-2 px-3 text-ink-gray-5 font-medium">{{ __('Сумма (TJS)') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(row, idx) in currentRows"
            :key="idx"
            class="border-b hover:bg-surface-gray-1 transition-colors"
          >
            <td class="py-2 px-3 text-ink-gray-8">{{ row.shop }}</td>
            <td class="py-2 px-3 text-ink-gray-6">{{ row.direction }}</td>
            <td v-if="activeTab === 'plan'" class="py-2 px-3 text-ink-gray-6">
              {{ monthName(row.month) }} {{ row.year }}
            </td>
            <td class="py-2 px-3 text-ink-gray-6">{{ row.manager }}</td>
            <td class="py-2 px-3 text-right font-medium text-ink-gray-8">
              {{ formatMoney(row.amount) }}
            </td>
          </tr>
        </tbody>
        <tfoot>
          <tr class="border-t-2">
            <td colspan="2" class="py-2 px-3 text-ink-gray-5 text-sm font-medium">
              {{ __('Итого') }}
            </td>
            <td v-if="activeTab === 'plan'" />
            <td class="py-2 px-3 text-ink-gray-5" />
            <td class="py-2 px-3 text-right font-semibold text-ink-gray-9">
              {{ formatMoney(totalAmount) }}
            </td>
          </tr>
        </tfoot>
      </table>
    </div>
  </div>
</template>

<script setup>
import SalesIcon from '@/components/Icons/SalesIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { call, Breadcrumbs } from 'frappe-ui'
import { ref, computed, onMounted } from 'vue'

const breadcrumbs = [{ label: __('Продажи'), route: { name: 'Sales' } }]

const tabs = [
  { key: 'day',     label: __('День') },
  { key: 'week',    label: __('Неделя') },
  { key: 'month',   label: __('Месяц') },
  { key: 'quarter', label: __('Квартал') },
  { key: 'year',    label: __('Год') },
  { key: 'plan',    label: __('План') },
]

const MONTHS = ['Янв','Фев','Мар','Апр','Май','Июн','Июл','Авг','Сен','Окт','Ноя','Дек']
function monthName(n) { return MONTHS[(n || 1) - 1] || n }

const activeTab = ref('month')
const loading = ref(false)
const error = ref(null)
const salesData = ref({})

const counts = computed(() => {
  const result = {}
  for (const tab of tabs) {
    const rows = salesData.value[tab.key] || []
    if (rows.length) result[tab.key] = rows.length
  }
  return result
})

const currentRows = computed(() => salesData.value[activeTab.value] || [])

const totalAmount = computed(() =>
  currentRows.value.reduce((sum, r) => sum + (r.amount || 0), 0)
)

function formatMoney(val) {
  if (!val) return '0'
  return Number(val).toLocaleString('ru-RU', { maximumFractionDigits: 2 })
}

async function loadData() {
  loading.value = true
  error.value = null
  try {
    salesData.value = await call('crm.integrations.sales_api.get_sales_data')
  } catch (e) {
    error.value = e?.messages?.[0] || __('Не удалось загрузить данные')
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

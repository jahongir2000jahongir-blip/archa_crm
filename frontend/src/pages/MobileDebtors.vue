<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
  </LayoutHeader>

  <div class="flex h-full flex-col">
    <!-- Stats -->
    <div class="grid grid-cols-2 gap-3 p-4 border-b">
      <div class="rounded-lg border p-3 text-center">
        <div class="text-xs text-ink-gray-5">{{ __('Общий долг') }}</div>
        <div class="mt-1 text-sm font-semibold text-ink-gray-9">
          {{ formatMoney(stats.total_debt) }} TJS
        </div>
      </div>
      <div class="rounded-lg border p-3 text-center">
        <div class="text-xs text-ink-gray-5">{{ __('Просрочено') }}</div>
        <div class="mt-1 text-sm font-semibold" :class="stats.overdue_count > 0 ? 'text-orange-500' : 'text-ink-gray-9'">
          {{ stats.overdue_count }}
        </div>
      </div>
      <div class="rounded-lg border p-3 text-center">
        <div class="text-xs text-ink-gray-5">{{ __('Критических') }}</div>
        <div class="mt-1 text-sm font-semibold" :class="stats.critical_count > 0 ? 'text-red-600' : 'text-ink-gray-9'">
          {{ stats.critical_count }}
        </div>
      </div>
      <div class="rounded-lg border p-3 text-center">
        <div class="text-xs text-ink-gray-5">{{ __('Без комм.') }}</div>
        <div class="mt-1 text-sm font-semibold text-ink-gray-9">
          {{ stats.no_comment_count }}
        </div>
      </div>
    </div>

    <div class="flex-1 overflow-auto">
      <div class="p-4">
        <div v-if="debtors.data?.data?.length" class="space-y-3">
          <div
            v-for="item in debtors.data.data"
            :key="item.name"
            class="rounded-lg border p-4"
          >
            <div class="text-base font-medium text-ink-gray-9">
              {{ item.contractor }}
            </div>
            <div class="mt-1 text-sm text-ink-gray-5">
              {{ item.manager }}
            </div>
            <div class="mt-2 flex items-center justify-between">
              <span class="text-sm font-semibold text-ink-gray-9">
                {{ formatMoney(item.debt_amount) }} TJS
              </span>
              <span
                v-if="item.days_overdue > 0"
                class="text-xs px-2 py-0.5 rounded-full"
                :class="item.days_overdue > 30 ? 'bg-red-100 text-red-600' : 'bg-orange-100 text-orange-600'"
              >
                {{ item.days_overdue }} дн. проср.
              </span>
            </div>
          </div>

          <ListFooter
            v-model="pageCount"
            class="border-t px-3 py-2"
            :options="{
              rowCount: debtors.data?.row_count,
              totalCount: debtors.data?.total_count,
            }"
          />
        </div>

        <div v-else-if="debtors.data" class="text-base text-ink-gray-5 text-center py-8">
          {{ __('Дебиторов не найдено') }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import { createListResource, createResource } from 'frappe-ui'
import { Breadcrumbs, ListFooter } from 'frappe-ui'
import { computed, reactive } from 'vue'

const breadcrumbs = [{ label: __('Дебиторы'), route: { name: 'Debtors' } }]

const stats = reactive({
  total_debt: 0,
  overdue_count: 0,
  critical_count: 0,
  no_comment_count: 0,
})

createResource({
  url: 'crm.integrations.one_c_sync.get_debtor_stats',
  auto: true,
  onSuccess: (data) => Object.assign(stats, data),
})

const debtors = createListResource({
  doctype: 'CRM Debtor',
  fields: ['name', 'contractor', 'manager', 'debt_amount', 'days_overdue', 'status'],
  orderBy: 'modified desc',
  pageLength: 20,
  auto: true,
})

const pageCount = computed({
  get: () => debtors.data?.page_length_count || 20,
  set: (val) => {
    debtors.update({ pageLength: val })
    debtors.reload()
  },
})

function formatMoney(val) {
  if (!val) return '0'
  return Number(val).toLocaleString('ru-RU', { maximumFractionDigits: 2 })
}
</script>

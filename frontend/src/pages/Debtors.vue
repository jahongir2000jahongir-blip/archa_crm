<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
    <template #right-header>
      <Button
        variant="solid"
        :label="__('Синхронизировать из 1С')"
        iconLeft="refresh-cw"
        :loading="syncLoading"
        @click="syncFrom1C"
      />
    </template>
  </LayoutHeader>

  <div class="flex flex-col h-full">
    <!-- Stats bar -->
    <div class="flex gap-4 px-5 py-3 border-b bg-surface-white flex-wrap">
      <div class="flex flex-col items-center min-w-[100px]">
        <span class="text-xs text-ink-gray-5 mb-0.5">{{ __('Общий долг') }}</span>
        <span class="text-base font-semibold text-ink-gray-9">
          {{ formatMoney(stats.total_debt) }} TJS
        </span>
      </div>
      <div class="w-px bg-gray-200 self-stretch" />
      <div class="flex flex-col items-center min-w-[80px]">
        <span class="text-xs text-ink-gray-5 mb-0.5">{{ __('Просрочено') }}</span>
        <span class="text-base font-semibold" :class="stats.overdue_count > 0 ? 'text-orange-500' : 'text-ink-gray-9'">
          {{ stats.overdue_count }}
        </span>
      </div>
      <div class="w-px bg-gray-200 self-stretch" />
      <div class="flex flex-col items-center min-w-[80px]">
        <span class="text-xs text-ink-gray-5 mb-0.5">{{ __('Критических') }}</span>
        <span class="text-base font-semibold" :class="stats.critical_count > 0 ? 'text-red-600' : 'text-ink-gray-9'">
          {{ stats.critical_count }}
        </span>
      </div>
      <div class="w-px bg-gray-200 self-stretch" />
      <div class="flex flex-col items-center min-w-[80px]">
        <span class="text-xs text-ink-gray-5 mb-0.5">{{ __('Без комм.') }}</span>
        <span class="text-base font-semibold text-ink-gray-9">
          {{ stats.no_comment_count }}
        </span>
      </div>
    </div>

    <ViewControls
      ref="viewControls"
      v-model="debtors"
      v-model:loadMore="loadMore"
      v-model:resizeColumn="triggerResize"
      v-model:updatedPageCount="updatedPageCount"
      doctype="CRM Debtor"
    />

    <DebtorsListView
      v-if="debtors.data && debtors.data.data && rows.length"
      ref="debtorsListView"
      v-model="debtors.data.page_length_count"
      v-model:list="debtors"
      :rows="rows"
      :columns="columns"
      :options="{
        showTooltip: false,
        resizeColumn: true,
        rowCount: debtors.data.row_count,
        totalCount: debtors.data.total_count,
      }"
      @loadMore="() => loadMore++"
      @columnWidthUpdated="() => triggerResize++"
      @updatePageCount="(count) => (updatedPageCount = count)"
      @applyFilter="(data) => viewControls.applyFilter(data)"
      @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
      @likeDoc="(data) => viewControls.likeDoc(data)"
      @selectionsChanged="(selections) => viewControls.updateSelections(selections)"
    />

    <EmptyState
      v-else-if="debtors.data && (!debtors.data.data || !rows.length)"
      name="Дебиторы"
      :icon="DebtorsIcon"
    />
  </div>
</template>

<script setup>
import DebtorsIcon from '@/components/Icons/DebtorsIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import DebtorsListView from '@/components/ListViews/DebtorsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import ViewControls from '@/components/ViewControls.vue'
import { getMeta } from '@/stores/meta'
import { formatDate, timeAgo } from '@/utils'
import { ref, computed, reactive } from 'vue'
import { createResource, call, toast } from 'frappe-ui'
import { Breadcrumbs } from 'frappe-ui'

const { getFormattedFloat } = getMeta('CRM Debtor')

const debtorsListView = ref(null)
const viewControls = ref(null)
const syncLoading = ref(false)

const breadcrumbs = [{ label: __('Дебиторы'), route: { name: 'Debtors' } }]

const debtors = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)

const stats = reactive({
  total_debt: 0,
  overdue_count: 0,
  critical_count: 0,
  no_comment_count: 0,
  total_count: 0,
})

const statsResource = createResource({
  url: 'crm.integrations.one_c_sync.get_debtor_stats',
  auto: true,
  onSuccess: (data) => {
    Object.assign(stats, data)
  },
})

function formatMoney(val) {
  if (!val) return '0'
  return Number(val).toLocaleString('ru-RU', { maximumFractionDigits: 2 })
}

const rows = computed(() => {
  if (!debtors.value?.data?.data) return []
  const view_type = debtors.value.data.view_type || 'list'
  if (!['list', 'group_by'].includes(view_type)) return []

  return debtors.value.data.data.map((item) => {
    let _rows = {}
    debtors.value?.data.rows.forEach((row) => {
      _rows[row] = item[row]

      let fieldType = debtors.value?.data.columns?.find(
        (col) => (col.key || col.value) == row,
      )?.type

      if (fieldType && fieldType === 'Currency') {
        _rows[row] = formatMoney(item[row])
      }

      if (fieldType && fieldType === 'Float') {
        _rows[row] = getFormattedFloat(row, item)
      }

      if (['modified', 'creation'].includes(row)) {
        _rows[row] = {
          label: formatDate(item[row]),
          timeAgo: __(timeAgo(item[row])),
        }
      }
    })
    return _rows
  })
})

const columns = computed(() => {
  let _columns = debtors.value?.data?.columns || []
  if (_columns.length) {
    _columns = _columns.map((col, index) => {
      if (index === _columns.length - 1) return { ...col, align: 'right' }
      return col
    })
  }
  return _columns
})

async function syncFrom1C() {
  syncLoading.value = true
  try {
    const result = await call('crm.integrations.one_c_sync.sync_from_1c')
    if (result.success) {
      statsResource.reload()
      if (debtors.value?.reload) debtors.value.reload()
      toast.success(__(`Синхронизировано дебиторов: ${result.debtors_synced}`))
    }
  } catch (error) {
    toast.error(error?.messages?.[0] || __('Не удалось синхронизировать данные из 1С'))
  } finally {
    syncLoading.value = false
  }
}
</script>

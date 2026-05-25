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
    <CategoryTabs
      v-model="activeCategory"
      :categories="categoryList"
      :counts="categoryCounts"
    />

    <ViewControls
      ref="viewControls"
      v-model="warehouses"
      v-model:loadMore="loadMore"
      v-model:resizeColumn="triggerResize"
      v-model:updatedPageCount="updatedPageCount"
      doctype="CRM Warehouse Item"
    />

    <WarehousesListView
      v-if="warehouses.data && warehouses.data.data && rows.length"
      ref="warehousesListView"
      v-model="warehouses.data.page_length_count"
      v-model:list="warehouses"
      :rows="rows"
      :columns="columns"
      :options="{
        showTooltip: false,
        resizeColumn: true,
        rowCount: warehouses.data.row_count,
        totalCount: warehouses.data.total_count,
      }"
      @loadMore="() => loadMore++"
      @columnWidthUpdated="() => triggerResize++"
      @updatePageCount="(count) => (updatedPageCount = count)"
      @applyFilter="(data) => viewControls.applyFilter(data)"
      @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
      @likeDoc="(data) => viewControls.likeDoc(data)"
      @selectionsChanged="
        (selections) => viewControls.updateSelections(selections)
      "
    />

    <EmptyState
      v-else-if="warehouses.data && warehouses.data.data && !rows.length"
      name="Склад"
      :icon="WarehousesIcon"
    />

    <EmptyState
      v-else-if="warehouses.data && !warehouses.data.data"
      name="Склад"
      :icon="WarehousesIcon"
    />
  </div>
</template>

<script setup>
import WarehousesIcon from '@/components/Icons/WarehousesIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import WarehousesListView from '@/components/ListViews/WarehousesListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import ViewControls from '@/components/ViewControls.vue'
import CategoryTabs from '@/components/Warehouse/CategoryTabs.vue'
import { getMeta } from '@/stores/meta'
import { formatDate, timeAgo } from '@/utils'
import { ref, computed, watch } from 'vue'
import { createResource, call } from 'frappe-ui'
import { Breadcrumbs } from 'frappe-ui'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('CRM Warehouse Item')

const warehousesListView = ref(null)
const viewControls = ref(null)
const syncLoading = ref(false)

const activeCategory = ref('All')

const categoryList = [
  { label: 'Все', value: 'All' },
  { label: 'Краски', value: 'Краски' },
  { label: 'Мебель', value: 'Мебель' },
  { label: 'Дверь', value: 'Дверь' },
  { label: 'Строительство', value: 'Строительство' },
  { label: 'Столы и стулья', value: 'Столы и стулья' },
  { label: 'Спорттовар', value: 'Спорттовар' },
  { label: 'Электрика', value: 'Электрика' },
  { label: 'Прочее', value: 'Прочее' },
]

const categoryCounts = ref({
  All: 0,
  Краски: 0,
  Мебель: 0,
  Дверь: 0,
  Строительство: 0,
  'Столы и стулья': 0,
  Спорттовар: 0,
  Электрика: 0,
  Прочее: 0,
})

const breadcrumbs = [
  { label: __('Склад'), route: { name: 'Warehouses' } },
]

const warehouses = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)

watch(activeCategory, () => {
  loadMore.value++
  if (!viewControls.value) return

  let currentFilters = { ...(warehouses.value.params?.filters || {}) }

  if (activeCategory.value === 'All') {
    delete currentFilters.category
  } else {
    currentFilters.category = activeCategory.value
  }

  viewControls.value.updateFilter(currentFilters)
})

const rows = computed(() => {
  if (!warehouses.value?.data?.data) return []
  const view_type = warehouses.value.data.view_type || 'list'
  if (!['list', 'group_by'].includes(view_type)) return []

  return warehouses.value.data.data.map((item) => {
    let _rows = {}
    warehouses.value?.data.rows.forEach((row) => {
      _rows[row] = item[row]

      let fieldType = warehouses.value?.data.columns?.find(
        (col) => (col.key || col.value) == row,
      )?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(item[row], '', true, fieldType == 'Datetime')
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, item)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, item)
      }

      if (fieldType && fieldType == 'Int') {
        _rows[row] = Math.round(item[row] ?? 0)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, item)
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
  let _columns = warehouses.value?.data?.columns || []

  if (_columns.length) {
    _columns = _columns.map((col, index) => {
      if (index === _columns.length - 1) {
        return { ...col, align: 'right' }
      }
      return col
    })
  }

  return _columns
})

const countsResource = createResource({
  url: 'crm.integrations.one_c_sync.get_warehouse_item_counts',
  auto: true,
  onSuccess: (data) => {
    categoryCounts.value = {
      All: data.All || 0,
      Краски: data['Краски'] || 0,
      Мебель: data['Мебель'] || 0,
      Дверь: data['Дверь'] || 0,
      Строительство: data['Строительство'] || 0,
      'Столы и стулья': data['Столы и стулья'] || 0,
      Спорттовар: data['Спорттовар'] || 0,
      Электрика: data['Электрика'] || 0,
      Прочее: data['Прочее'] || 0,
    }
  },
})

async function syncFrom1C() {
  syncLoading.value = true
  try {
    const result = await call('crm.integrations.one_c_sync.sync_from_1c')
    if (result.success) {
      countsResource.reload()
      if (warehouses.value?.reload) {
        warehouses.value.reload()
      }
    }
  } catch (error) {
    console.error('Sync failed:', error)
  } finally {
    syncLoading.value = false
  }
}
</script>

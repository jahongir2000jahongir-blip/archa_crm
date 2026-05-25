<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
  </LayoutHeader>

  <div class="flex h-full">
    <div class="flex-1 overflow-auto">
      <div class="p-6">
        <div class="mb-6">
          <h1 class="text-2xl font-semibold text-ink-gray-9">
            {{ warehouse.doc?.warehouse_name }}
          </h1>
          <p v-if="warehouse.doc?.one_c_name" class="text-base text-ink-gray-5 mt-1">
            {{ __('1C:') }} {{ warehouse.doc.one_c_name }}
          </p>
        </div>

        <div class="mb-8">
          <h2 class="text-lg font-medium text-ink-gray-9 mb-4">
            {{ __('Товары на складе') }}
          </h2>

          <ListView
            v-if="items.data?.data?.length"
            :columns="itemColumns"
            :rows="itemRows"
            :options="{ selectable: false, showTooltip: false }"
            row-key="name"
          >
            <ListHeader>
              <ListHeaderItem
                v-for="column in itemColumns"
                :key="column.key"
                :item="column"
              />
            </ListHeader>
            <ListRows :rows="itemRows" doctype="CRM Warehouse Item">
              <template #default="{ idx, column, item }">
                <div class="truncate text-base">
                  {{ item }}
                </div>
              </template>
            </ListRows>
            <ListFooter
              v-model="pageCount"
              class="border-t px-3 py-2"
              :options="{
                rowCount: items.data?.row_count,
                totalCount: items.data?.total_count,
              }"
            />
          </ListView>

          <div v-else-if="items.data" class="text-base text-ink-gray-5 text-center py-8">
            {{ __('Товаров на этом складе нет') }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import { useDocument } from '@/data/document'
import { createListResource } from 'frappe-ui'
import {
  Breadcrumbs,
  ListView,
  ListHeader,
  ListHeaderItem,
  ListRows,
  ListFooter,
} from 'frappe-ui'
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const warehouseId = route.params.warehouseId

const { document: warehouse } = useDocument('CRM Warehouse', warehouseId)

const breadcrumbs = computed(() => [
  { label: __('Склад'), route: { name: 'Warehouses' } },
  { label: warehouse.doc?.warehouse_name || warehouseId, route: {} },
])

const items = createListResource({
  doctype: 'CRM Warehouse Item',
  fields: [
    'name', 'item_name', 'article', 'category', 'quantity',
    'reserved', 'price', 'price_usd', 'warehouse_name',
  ],
  filters: { warehouse: warehouseId },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: warehouseId ? true : false,
})

const itemColumns = computed(() => [
  { label: 'Наименование', key: 'item_name', width: '16rem' },
  { label: 'Артикул', key: 'article', width: '10rem' },
  { label: 'Категория', key: 'category', width: '12rem' },
  { label: 'Количество', key: 'quantity', width: '8rem' },
  { label: 'Резерв', key: 'reserved', width: '8rem' },
  { label: 'Цена (TJS)', key: 'price', width: '10rem' },
  { label: 'Цена (USD)', key: 'price_usd', width: '10rem' },
])

const itemRows = computed(() => {
  if (!items.data?.data) return []
  return items.data.data.map((item) => ({
    name: item.name,
    item_name: item.item_name,
    article: item.article || '-',
    category: item.category,
    quantity: item.quantity,
    reserved: item.reserved,
    price: item.price,
    price_usd: item.price_usd,
  }))
})

const pageCount = computed({
  get: () => items.data?.page_length_count || 20,
  set: (val) => {
    items.update({ pageLength: val })
    items.reload()
  },
})
</script>

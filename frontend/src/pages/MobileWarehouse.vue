<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
  </LayoutHeader>

  <div class="flex h-full">
    <div class="flex-1 overflow-auto">
      <div class="p-4">
        <div class="mb-4">
          <h1 class="text-xl font-semibold text-ink-gray-9">
            {{ warehouse.doc?.warehouse_name }}
          </h1>
        </div>

        <div v-if="items.data?.data?.length" class="space-y-3">
          <div
            v-for="item in items.data.data"
            :key="item.name"
            class="rounded-lg border p-4"
          >
            <div class="text-base font-medium text-ink-gray-9">
              {{ item.item_name }}
            </div>
            <div class="mt-2 text-sm text-ink-gray-5">
              <span>{{ item.category }}</span>
              <span class="mx-2">|</span>
              <span>{{ item.quantity }} {{ item.unit }}</span>
            </div>
            <div class="mt-1 text-sm text-ink-gray-7">
              {{ item.price }} TJS
            </div>
          </div>

          <ListFooter
            v-model="pageCount"
            class="border-t px-3 py-2"
            :options="{
              rowCount: items.data?.row_count,
              totalCount: items.data?.total_count,
            }"
          />
        </div>

        <div v-else-if="items.data" class="text-base text-ink-gray-5 text-center py-8">
          {{ __('Товаров не найдено') }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import { useDocument } from '@/data/document'
import { createListResource } from 'frappe-ui'
import { Breadcrumbs, ListFooter } from 'frappe-ui'
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
  fields: ['name', 'item_name', 'category', 'quantity', 'unit', 'price'],
  filters: { warehouse: warehouseId },
  orderBy: 'modified desc',
  pageLength: 20,
  auto: warehouseId ? true : false,
})

const pageCount = computed({
  get: () => items.data?.page_length_count || 20,
  set: (val) => {
    items.update({ pageLength: val })
    items.reload()
  },
})
</script>

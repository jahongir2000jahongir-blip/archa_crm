<template>
  <ListView
    :columns="columns"
    :rows="rows"
    :options="{
      getRowRoute: () => null,
      selectable: options.selectable,
      showTooltip: options.showTooltip,
      resizeColumn: options.resizeColumn,
    }"
    row-key="name"
    @update:selections="(selections) => emit('selectionsChanged', selections)"
  >
    <ListHeader
      class="sm:mx-5 mx-3"
      @columnWidthUpdated="emit('columnWidthUpdated')"
    >
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
        @columnWidthUpdated="emit('columnWidthUpdated', column)"
      />
    </ListHeader>
    <ListRows
      v-slot="{ idx, column, item, row }"
      class="mx-3 sm:mx-5"
      :rows="rows"
      doctype="CRM RKO Request"
    >
      <ListRowItem :item="item" :align="column.align" class="overflow-hidden">
        <template #default="{ label }">
          <div
            v-if="['modified', 'creation'].includes(column.key)"
            class="truncate text-base"
          >
            <Tooltip :text="item.label">
              <div>{{ item.timeAgo }}</div>
            </Tooltip>
          </div>
          <div
            v-else-if="column.key === 'status'"
            class="truncate text-base"
          >
            <span
              class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium"
              :class="statusClass(label)"
            >
              {{ label }}
            </span>
          </div>
          <div
            v-else-if="column.key === 'purpose'"
            class="truncate text-base cursor-pointer hover:text-blue-600 hover:underline"
            @click.stop="emit('rowClicked', row)"
          >
            {{ label }}
          </div>
          <div
            v-else-if="column.key === 'approver_comment' && label"
            class="truncate text-base text-ink-gray-5 italic"
          >
            {{ label }}
          </div>
          <div
            v-else-if="label"
            class="truncate text-base"
            @click="
              (event) =>
                emit('applyFilter', {
                  event,
                  idx,
                  column,
                  item,
                  firstColumn: columns[0],
                })
            "
          >
            {{ label }}
          </div>
        </template>
      </ListRowItem>
    </ListRows>
    <ListSelectBanner>
      <template #actions="{ selections, unselectAll }">
        <Dropdown
          :options="listBulkActionsRef.bulkActions(selections, unselectAll)"
        >
          <Button icon="more-horizontal" variant="ghost" />
        </Dropdown>
      </template>
    </ListSelectBanner>
  </ListView>
  <ListFooter
    v-model="pageLengthCount"
    class="border-t sm:px-5 px-3 py-2"
    :options="{
      rowCount: options.rowCount,
      totalCount: options.totalCount,
    }"
    @loadMore="emit('loadMore')"
  />
  <ListBulkActions
    ref="listBulkActionsRef"
    v-model="list"
    doctype="CRM RKO Request"
    :options="{ hideAssign: true }"
  />
</template>

<script setup>
import ListBulkActions from '@/components/ListBulkActions.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import {
  ListView,
  ListHeader,
  ListHeaderItem,
  ListSelectBanner,
  ListRowItem,
  ListFooter,
  Tooltip,
  Dropdown,
} from 'frappe-ui'
import { ref, watch } from 'vue'

defineProps({
  rows: { type: Array, required: true },
  columns: { type: Array, required: true },
  options: {
    type: Object,
    default: () => ({
      selectable: true,
      showTooltip: true,
      resizeColumn: false,
      totalCount: 0,
      rowCount: 0,
    }),
  },
})

const emit = defineEmits([
  'loadMore',
  'updatePageCount',
  'columnWidthUpdated',
  'applyFilter',
  'applyLikeFilter',
  'likeDoc',
  'selectionsChanged',
  'rowClicked',
])

const pageLengthCount = defineModel({ type: Number })
const list = defineModel('list', { type: Object })
const listBulkActionsRef = ref(null)

function statusClass(status) {
  if (status === 'Оплачено') return 'bg-green-50 text-green-700 ring-1 ring-inset ring-green-600/20'
  if (status === 'Отклонена') return 'bg-red-50 text-red-700 ring-1 ring-inset ring-red-600/20'
  if (status === 'У кассира') return 'bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-600/20'
  return 'bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-600/20'
}

watch(pageLengthCount, (val, old_value) => {
  if (val === old_value) return
  emit('updatePageCount', val)
})
</script>

<style scoped>
:deep(.w-max.min-w-full) {
  width: 100% !important;
}
:deep(.grid.items-center > *) {
  min-width: 0;
}
</style>

<template>
  <Dialog v-model="show" :options="{ size: 'xl' }">
    <template #body>
      <div class="px-4 pt-5 pb-6 bg-surface-modal sm:px-6">
        <div class="flex items-center justify-between mb-5">
          <div>
            <h3 class="text-2xl font-semibold leading-6 text-ink-gray-9">
              {{ __('Новый склад') }}
            </h3>
          </div>
          <div class="flex items-center gap-1">
            <Button
              variant="ghost"
              class="w-7"
              icon="x"
              @click="show = false"
            />
          </div>
        </div>
        <FieldLayout
          v-if="tabs.data?.length"
          :tabs="tabs.data"
          :data="warehouse.doc"
          doctype="CRM Warehouse"
        />
        <ErrorMessage v-if="error" class="mt-8" :message="__(error)" />
      </div>
      <div class="px-4 pt-4 pb-7 sm:px-6">
        <div class="space-y-2">
          <Button
            class="w-full"
            variant="solid"
            :label="__('Create')"
            :loading="loading"
            @click="createWarehouse"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import FieldLayout from '@/components/FieldLayout/FieldLayout.vue'
import { useDocument } from '@/data/document'
import { call } from 'frappe-ui'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  data: { type: Object, default: () => ({}) },
  options: {
    type: Object,
    default: () => ({ redirect: true, afterInsert: () => {} }),
  },
})

const router = useRouter()
const show = defineModel({ type: Boolean })

const loading = ref(false)
const error = ref(null)

const { document: warehouse, triggerOnBeforeCreate } =
  useDocument('CRM Warehouse')

async function createWarehouse() {
  loading.value = true
  error.value = null

  await triggerOnBeforeCreate?.()

  const doc = await call(
    'frappe.client.insert',
    {
      doc: {
        doctype: 'CRM Warehouse',
        ...warehouse.doc,
      },
    },
    {
      onError: (err) => {
        error.value = err.error?.messages?.[0]
        loading.value = false
      },
    },
  )
  loading.value = false
  if (doc.name) {
    handleWarehouseUpdate(doc)
    warehouse.doc = {}
  }
}

function handleWarehouseUpdate(doc) {
  if (doc.name && props.options.redirect) {
    router.push({
      name: 'Warehouse',
      params: { warehouseId: doc.name },
    })
  }
  show.value = false
  props.options.afterInsert?.(doc)
}

const tabs = ref({})
</script>

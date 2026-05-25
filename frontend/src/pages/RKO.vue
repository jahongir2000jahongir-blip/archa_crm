<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs :items="breadcrumbs" />
    </template>
  </LayoutHeader>

  <div class="flex flex-col h-full">
    <CategoryTabs
      v-model="activeTab"
      :categories="tabList"
      :counts="tabCounts"
    />

    <div class="px-5 py-3 border-b">
      <Button
        variant="solid"
        :label="__('Новая заявка РКО')"
        icon-left="plus"
        @click="openNewDialog"
      />
    </div>

    <ViewControls
      ref="viewControls"
      v-model="requests"
      v-model:loadMore="loadMore"
      v-model:resizeColumn="triggerResize"
      v-model:updatedPageCount="updatedPageCount"
      doctype="CRM RKO Request"
      :options="{ hideFilter: !isManager() }"
    />

    <RKOListView
      v-if="requests.data && requests.data.data && rows.length"
      ref="rkoListView"
      v-model="requests.data.page_length_count"
      v-model:list="requests"
      :rows="rows"
      :columns="columns"
      :options="{
        showTooltip: false,
        resizeColumn: true,
        rowCount: requests.data.row_count,
        totalCount: requests.data.total_count,
      }"
      @loadMore="() => loadMore++"
      @columnWidthUpdated="() => triggerResize++"
      @updatePageCount="(count) => (updatedPageCount = count)"
      @applyFilter="(data) => viewControls.applyFilter(data)"
      @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
      @selectionsChanged="(selections) => viewControls.updateSelections(selections)"
      @rowClicked="(row) => openDetail(row)"
    />

    <EmptyState
      v-else-if="requests.data && (!requests.data.data || !rows.length)"
      name="РКО"
      :icon="RKOIcon"
    />
  </div>

  <!-- New RKO Request Dialog -->
  <Dialog v-model="showNewDialog" :options="{ title: __('Новая заявка РКО'), size: 'md' }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <label class="text-sm text-ink-gray-5">{{ __('Заявитель') }}</label>
          <div class="flex h-8 w-full items-center rounded border border-outline-gray-2 bg-surface-gray-1 px-2.5 text-base text-ink-gray-7 cursor-not-allowed">
            {{ getUser(user).full_name || user }}
          </div>
        </div>

        <FormControl
          v-model="newRequest.purpose"
          :label="__('Назначение платежа')"
          type="text"
          :placeholder="__('Введите назначение платежа')"
          required
        />

        <FormControl
          v-model="newRequest.amount"
          :label="__('Сумма (сомони)')"
          type="number"
          :placeholder="__('0.00')"
          min="0"
          step="0.01"
        />

        <div class="flex flex-col gap-1.5">
          <label class="text-sm text-ink-gray-5">{{ __('Статья расходов') }}</label>
          <Popover v-model:show="showCategoryDropdown" class="w-full">
            <template #target>
              <button
                type="button"
                class="flex h-8 w-full items-center justify-between rounded border border-outline-gray-2 bg-surface-white px-2.5 py-1.5 text-base transition-colors hover:border-outline-gray-3 hover:shadow-sm"
                @click="showCategoryDropdown = !showCategoryDropdown"
              >
                <span :class="newRequest.expense_category ? 'text-ink-gray-8' : 'text-ink-gray-4'">
                  {{ newRequest.expense_category || __('Выберите статью расходов') }}
                </span>
                <FeatherIcon name="chevron-down" class="h-4 w-4 text-ink-gray-5 shrink-0" />
              </button>
            </template>
            <template #body>
              <div class="mt-1 rounded-lg bg-surface-modal shadow-2xl py-1.5 min-w-[240px]">
                <ul class="max-h-48 overflow-y-auto px-1.5">
                  <li
                    v-for="opt in expenseCategoryOptions"
                    :key="opt"
                    class="cursor-pointer rounded px-2.5 py-1.5 text-base text-ink-gray-7 hover:bg-surface-gray-3"
                    @click="() => { newRequest.expense_category = opt; showCategoryDropdown = false }"
                  >
                    {{ opt }}
                  </li>
                </ul>
              </div>
            </template>
          </Popover>
        </div>

        <FormControl
          v-model="newRequest.recipient"
          :label="__('Получатель / поставщик')"
          type="text"
          :placeholder="__('ООО...')"
        />

        <div class="flex flex-col gap-1.5">
          <label class="text-sm text-ink-gray-5">{{ __('Дата создания') }}</label>
          <input
            type="date"
            :value="newRequest.payment_date"
            readonly
            class="w-full rounded border border-gray-200 bg-surface-gray-1 px-3 py-1.5 text-sm text-ink-gray-7 cursor-not-allowed"
          />
        </div>

        <FormControl
          v-model="newRequest.comment"
          :label="__('Комментарий')"
          type="textarea"
          :placeholder="__('Введите комментарий')"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex items-center gap-2 w-full">
        <span class="text-sm text-ink-gray-5 whitespace-nowrap">{{ __('Кому:') }}</span>
        <div class="flex gap-1">
          <button
            class="px-3 py-1.5 rounded text-sm transition-colors"
            :class="newRequest.approver_role === 'Главный бухгалтер'
              ? 'bg-gray-800 text-white'
              : 'bg-surface-gray-2 text-ink-gray-7 hover:bg-surface-gray-3'"
            @click="newRequest.approver_role = 'Главный бухгалтер'"
          >
            {{ __('Гл. бухгалтер') }}
          </button>
          <button
            class="px-3 py-1.5 rounded text-sm transition-colors"
            :class="newRequest.approver_role === 'Директор'
              ? 'bg-gray-800 text-white'
              : 'bg-surface-gray-2 text-ink-gray-7 hover:bg-surface-gray-3'"
            @click="newRequest.approver_role = 'Директор'"
          >
            {{ __('Директор') }}
          </button>
        </div>
        <Button
          variant="solid"
          :label="__('Отправить')"
          :loading="createLoading"
          class="ml-auto"
          @click="createRequest"
        />
      </div>
    </template>
  </Dialog>

  <!-- Detail / Approval Dialog -->
  <Dialog v-model="showDetailDialog" :options="{ title: detailDoc?.name || '', size: 'md' }">
    <template #body-content>
      <div v-if="detailDoc" class="flex flex-col gap-3">
        <!-- Status badge -->
        <div class="flex items-center justify-between">
          <span class="text-sm text-ink-gray-5">{{ __('Статус') }}</span>
          <span
            class="inline-flex items-center px-2.5 py-1 rounded-full text-sm font-medium"
            :class="detailStatusClass(detailDoc.status)"
          >
            {{ detailDoc.status }}
          </span>
        </div>

        <div class="border-t pt-3 flex flex-col gap-2.5">
          <div v-if="detailDoc.created_by_name" class="flex justify-between gap-4">
            <span class="text-sm text-ink-gray-5 shrink-0">{{ __('Заявитель') }}</span>
            <span class="text-sm text-ink-gray-8">{{ detailDoc.created_by_name }}</span>
          </div>
          <div class="flex justify-between gap-4">
            <span class="text-sm text-ink-gray-5 shrink-0">{{ __('Назначение платежа') }}</span>
            <span class="text-sm text-ink-gray-8 text-right">{{ detailDoc.purpose }}</span>
          </div>
          <div v-if="detailDoc.amount" class="flex justify-between gap-4">
            <span class="text-sm text-ink-gray-5 shrink-0">{{ __('Сумма (сомони)') }}</span>
            <span class="text-sm text-ink-gray-8">{{ detailDoc.amount }}</span>
          </div>
          <div v-if="detailDoc.expense_category" class="flex justify-between gap-4">
            <span class="text-sm text-ink-gray-5 shrink-0">{{ __('Статья расходов') }}</span>
            <span class="text-sm text-ink-gray-8">{{ detailDoc.expense_category }}</span>
          </div>
          <div v-if="detailDoc.recipient" class="flex justify-between gap-4">
            <span class="text-sm text-ink-gray-5 shrink-0">{{ __('Получатель') }}</span>
            <span class="text-sm text-ink-gray-8">{{ detailDoc.recipient }}</span>
          </div>
          <div v-if="detailDoc.payment_date" class="flex justify-between gap-4">
            <span class="text-sm text-ink-gray-5 shrink-0">{{ __('Дата создания') }}</span>
            <span class="text-sm text-ink-gray-8">{{ detailDoc.payment_date }}</span>
          </div>
          <div v-if="detailDoc.approval_date" class="flex justify-between gap-4">
            <span class="text-sm text-ink-gray-5 shrink-0">{{ __('Дата согласования') }}</span>
            <span class="text-sm text-ink-gray-8">{{ detailDoc.approval_date }}</span>
          </div>
          <div v-if="detailDoc.approver_role" class="flex justify-between gap-4">
            <span class="text-sm text-ink-gray-5 shrink-0">{{ __('Отправлено') }}</span>
            <span class="text-sm text-ink-gray-8">{{ detailDoc.approver_role }}</span>
          </div>
          <div v-if="detailDoc.comment" class="flex flex-col gap-1 mt-1">
            <span class="text-sm text-ink-gray-5">{{ __('Комментарий заявителя') }}</span>
            <p class="text-sm text-ink-gray-8 bg-surface-gray-1 rounded p-2.5">{{ detailDoc.comment }}</p>
          </div>
        </div>

        <!-- Approver comment (rejection reason) -->
        <div
          v-if="detailDoc.approver_comment"
          class="rounded-lg border border-red-200 bg-red-50 p-3 flex flex-col gap-1"
        >
          <span class="text-xs font-medium text-red-600 uppercase tracking-wide">{{ __('Причина отклонения') }}</span>
          <p class="text-sm text-red-700">{{ detailDoc.approver_comment }}</p>
        </div>

        <!-- Approval actions for approvers only -->
        <div
          v-if="isManager() && userApproverRole && detailDoc.status === 'На одобрении' && detailDoc.approver_role === userApproverRole"
          class="border-t pt-3 flex flex-col gap-3"
        >
          <div class="flex gap-2 flex-wrap">
            <Button
              variant="solid"
              :label="__('Согласовать')"
              :loading="actionLoading"
              class="bg-green-600 hover:bg-green-700 border-green-600"
              @click="approveRequest"
            />
            <Button
              variant="outline"
              :label="__('Отклонить')"
              class="text-red-600 border-red-300 hover:bg-red-50"
              @click="showRejectInput = true; showRedirectInput = false"
            />
            <Button
              variant="outline"
              :label="detailDoc.approver_role === 'Главный бухгалтер' ? __('Перенаправить на директора') : __('Перенаправить на гл. бухгалтера')"
              @click="showRedirectInput = true; showRejectInput = false"
            />
          </div>

          <!-- Reject inline -->
          <div v-if="showRejectInput" class="flex flex-col gap-2">
            <span class="text-sm text-ink-gray-5">{{ __('Причина отклонения') }}</span>
            <FormControl
              v-model="rejectComment"
              type="textarea"
              :placeholder="__('Укажите причину отклонения...')"
              :rows="3"
            />
            <Button
              variant="solid"
              :label="__('Сохранить')"
              :loading="actionLoading"
              class="bg-red-600 hover:bg-red-700 border-red-600 self-start"
              @click="rejectRequest"
            />
          </div>

          <!-- Redirect inline -->
          <div v-if="showRedirectInput" class="flex flex-col gap-2">
            <span class="text-sm text-ink-gray-5">{{ __('Комментарий перенаправления') }}</span>
            <FormControl
              v-model="redirectComment"
              type="textarea"
              :placeholder="__('Укажите причину перенаправления...')"
              :rows="3"
            />
            <Button
              variant="solid"
              :label="__('Сохранить')"
              :loading="actionLoading"
              class="self-start"
              @click="redirectRequest"
            />
          </div>
        </div>

        <!-- Cashier actions -->
        <div
          v-if="userApproverRole === 'Кассир' && detailDoc.status === 'У кассира'"
          class="border-t pt-3"
        >
          <Button
            variant="solid"
            :label="__('Оплачено')"
            :loading="actionLoading"
            class="bg-emerald-600 hover:bg-emerald-700 border-emerald-600"
            @click="cashierMarkPaidRequest"
          />
        </div>

        <!-- Redirect comment display -->
        <div v-if="detailDoc.redirect_comment" class="rounded-lg border border-blue-200 bg-blue-50 p-3 flex flex-col gap-1">
          <span class="text-xs font-medium text-blue-600 uppercase tracking-wide">{{ __('Комментарий перенаправления') }}</span>
          <p class="text-sm text-blue-700">{{ detailDoc.redirect_comment }}</p>
        </div>
      </div>
      <div v-else class="py-8 text-center text-ink-gray-4">{{ __('Загрузка...') }}</div>
    </template>
  </Dialog>
</template>

<script setup>
import RKOIcon from '@/components/Icons/RKOIcon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import RKOListView from '@/components/ListViews/RKOListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import ViewControls from '@/components/ViewControls.vue'
import CategoryTabs from '@/components/Warehouse/CategoryTabs.vue'
import { sessionStore } from '@/stores/session'
import { usersStore } from '@/stores/users'
import { getMeta } from '@/stores/meta'
import { formatDate, timeAgo } from '@/utils'
import { ref, computed, reactive, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { createResource, call, toast, Breadcrumbs, Dialog, FormControl, Popover, FeatherIcon } from 'frappe-ui'
import { useRoute } from 'vue-router'

const { getFormattedCurrency } = getMeta('CRM RKO Request')
const { user } = sessionStore()
const { isManager, getUser } = usersStore()
const route = useRoute()

const rkoListView = ref(null)
const viewControls = ref(null)
const showNewDialog = ref(false)
const createLoading = ref(false)

const activeTab = ref(isManager() ? 'all' : 'my')
const userApproverRole = ref(null)

const tabList = computed(() => {
  if (isManager()) {
    const pendingLabel = userApproverRole.value === 'Кассир' ? 'К выдаче' : 'На одобрении'
    return [
      { label: 'Все', value: 'all' },
      { label: 'Мои заявки', value: 'my' },
      { label: pendingLabel, value: 'pending' },
    ]
  }
  return [
    { label: 'Мои заявки', value: 'my' },
  ]
})

const tabCounts = ref({ my: 0, all: 0, pending: 0 })

const expenseCategoryOptions = [
  'Материалы и сирье',
  'Зарплата / аванс',
  'Транспорт / топливо',
  'Аренда',
  'Коммунальные услуги',
  'Офисные расходы',
  'Ремонт и обслуживание',
  'Прочее',
]

const showCategoryDropdown = ref(false)
const breadcrumbs = [{ label: __('РКО'), route: { name: 'RKO' } }]

const requests = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)

// Detail dialog state
const showDetailDialog = ref(false)
const detailDoc = ref(null)
const showRejectInput = ref(false)
const showRedirectInput = ref(false)
const rejectComment = ref('')
const redirectComment = ref('')
const actionLoading = ref(false)

function todayDate() {
  return new Date().toISOString().split('T')[0]
}

const newRequest = reactive({
  purpose: '',
  amount: '',
  expense_category: '',
  recipient: '',
  payment_date: todayDate(),
  comment: '',
  approver_role: 'Главный бухгалтер',
})

function openNewDialog() {
  newRequest.purpose = ''
  newRequest.amount = ''
  newRequest.expense_category = ''
  newRequest.recipient = ''
  newRequest.payment_date = todayDate()
  newRequest.comment = ''
  newRequest.approver_role = 'Главный бухгалтер'
  showNewDialog.value = true
}

async function openDetail(row) {
  if (!row?.name) return
  showDetailDialog.value = true
  showRejectInput.value = false
  showRedirectInput.value = false
  rejectComment.value = ''
  redirectComment.value = ''
  detailDoc.value = null
  try {
    const doc = await call('crm.integrations.rko_api.get_rko_request', { name: row.name })
    detailDoc.value = doc
  } catch {
    toast.error(__('Не удалось загрузить заявку'))
    showDetailDialog.value = false
  }
}

async function approveRequest() {
  actionLoading.value = true
  try {
    await call('crm.integrations.rko_api.approve_rko_request', { name: detailDoc.value.name })
    toast.success(__('Заявка согласована'))
    showDetailDialog.value = false
    countsResource.reload()
    if (requests.value?.reload) requests.value.reload()
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Не удалось согласовать заявку'))
  } finally {
    actionLoading.value = false
  }
}

async function redirectRequest() {
  if (!redirectComment.value.trim()) {
    toast.error(__('Укажите причину перенаправления'))
    return
  }
  actionLoading.value = true
  try {
    await call('crm.integrations.rko_api.redirect_rko_request', {
      name: detailDoc.value.name,
      redirect_comment: redirectComment.value,
    })
    toast.success(__('Заявка перенаправлена'))
    showRedirectInput.value = false
    showDetailDialog.value = false
    redirectComment.value = ''
    countsResource.reload()
    if (requests.value?.reload) requests.value.reload()
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Не удалось перенаправить заявку'))
  } finally {
    actionLoading.value = false
  }
}

async function cashierMarkPaidRequest() {
  actionLoading.value = true
  try {
    await call('crm.integrations.rko_api.cashier_mark_paid_rko_request', { name: detailDoc.value.name })
    toast.success(__('Заявка отмечена как оплаченная'))
    showDetailDialog.value = false
    countsResource.reload()
    if (requests.value?.reload) requests.value.reload()
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Не удалось отметить оплату'))
  } finally {
    actionLoading.value = false
  }
}


async function rejectRequest() {
  if (!rejectComment.value.trim()) {
    toast.error(__('Укажите причину отклонения'))
    return
  }
  actionLoading.value = true
  try {
    await call('crm.integrations.rko_api.reject_rko_request', {
      name: detailDoc.value.name,
      approver_comment: rejectComment.value,
    })
    toast.success(__('Заявка отклонена'))
    showRejectInput.value = false
    showDetailDialog.value = false
    rejectComment.value = ''
    countsResource.reload()
    if (requests.value?.reload) requests.value.reload()
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Не удалось отклонить заявку'))
  } finally {
    actionLoading.value = false
  }
}

function detailStatusClass(status) {
  if (status === 'Оплачено') return 'bg-green-50 text-green-700 ring-1 ring-inset ring-green-600/20'
  if (status === 'Отклонена') return 'bg-red-50 text-red-700 ring-1 ring-inset ring-red-600/20'
  if (status === 'У кассира') return 'bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-600/20'
  return 'bg-amber-50 text-amber-700 ring-1 ring-inset ring-amber-600/20'
}

const countsResource = createResource({
  url: 'crm.integrations.rko_api.get_rko_counts',
  auto: true,
  onSuccess: (data) => {
    tabCounts.value = data
  },
})

function applyTabFilter(tab) {
  if (!viewControls.value) return
  let filters = {}
  let orFilters = null

  if (tab === 'my') {
    filters.owner = user
  } else if (tab === 'all' && userApproverRole.value === 'Директор') {
    // Директор видит только свои заявки и назначенные ему
    orFilters = [['owner', '=', user], ['approver_role', '=', 'Директор']]
  } else if (tab === 'pending') {
    if (userApproverRole.value === 'Кассир') {
      filters.status = 'У кассира'
    } else if (userApproverRole.value) {
      filters.approver_role = userApproverRole.value
      filters.status = 'На одобрении'
    } else {
      filters.owner = user
      filters.status = 'На одобрении'
    }
  }
  viewControls.value.updateFilter(filters, orFilters)
}

onMounted(async () => {
  try {
    userApproverRole.value = await call('crm.integrations.rko_api.get_user_approver_role')
  } catch {
    userApproverRole.value = null
  }
  await nextTick()
  applyTabFilter(activeTab.value)

  if (route.query.open) {
    openDetail({ name: route.query.open })
  }

  $socket.on('rko_updated', () => {
    countsResource.reload()
    if (requests.value?.reload) requests.value.reload()
  })
})

onUnmounted(() => {
  $socket.off('rko_updated')
})

watch(activeTab, (tab) => {
  applyTabFilter(tab)
})

async function createRequest() {
  if (!newRequest.purpose.trim()) {
    toast.error(__('Введите назначение платежа'))
    return
  }
  createLoading.value = true
  try {
    await call('crm.integrations.rko_api.create_rko_request', {
      purpose: newRequest.purpose,
      amount: newRequest.amount || 0,
      expense_category: newRequest.expense_category,
      recipient: newRequest.recipient,
      payment_date: newRequest.payment_date,
      comment: newRequest.comment,
      approver_role: newRequest.approver_role,
    })
    showNewDialog.value = false
    countsResource.reload()
    if (requests.value?.reload) requests.value.reload()
    toast.success(__('Заявка отправлена на одобрение'))
  } catch (error) {
    toast.error(error?.messages?.[0] || __('Не удалось создать заявку'))
  } finally {
    createLoading.value = false
  }
}

const rows = computed(() => {
  if (!requests.value?.data?.data) return []
  const view_type = requests.value.data.view_type || 'list'
  if (!['list', 'group_by'].includes(view_type)) return []

  return requests.value.data.data.map((item) => {
    let _rows = { name: item.name }
    requests.value?.data.rows.forEach((row) => {
      _rows[row] = item[row]

      let fieldType = requests.value?.data.columns?.find(
        (col) => (col.key || col.value) == row,
      )?.type

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation'].includes(row)
      ) {
        _rows[row] = formatDate(item[row], '', true, fieldType === 'Datetime')
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
  let _columns = requests.value?.data?.columns || []
  if (_columns.length) {
    _columns = _columns.map((col, index) => {
      if (index === _columns.length - 1) return { ...col, align: 'right' }
      return col
    })
  }
  return _columns
})
</script>

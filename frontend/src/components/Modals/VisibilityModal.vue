<template>
  <Dialog v-model="show" :options="{ size: 'md' }">
    <template #body-title>
      <div class="flex items-center gap-2">
        <FeatherIcon name="eye" class="h-5 w-5 text-ink-gray-6" />
        <span class="text-base font-semibold text-ink-gray-9">{{ __('Видимость') }}</span>
      </div>
    </template>
    <template #body-content>
      <div class="flex flex-col gap-4">

        <!-- User selector -->
        <div class="flex flex-col gap-1.5">
          <label class="text-sm text-ink-gray-5">{{ __('Пользователь') }}</label>
          <Popover v-model:show="showUserDropdown" class="w-full">
            <template #target>
              <button
                type="button"
                class="flex h-8 w-full items-center justify-between rounded border border-outline-gray-2 bg-surface-white px-2.5 py-1.5 text-base transition-colors hover:border-outline-gray-3 hover:shadow-sm"
                @click="showUserDropdown = !showUserDropdown"
              >
                <span :class="selectedUserLabel ? 'text-ink-gray-8' : 'text-ink-gray-4'">
                  {{ selectedUserLabel || __('Выберите пользователя') }}
                </span>
                <FeatherIcon name="chevron-down" class="h-4 w-4 text-ink-gray-5 shrink-0" />
              </button>
            </template>
            <template #body>
              <div class="mt-1 rounded-lg bg-surface-modal shadow-2xl py-1.5 min-w-[240px]">
                <ul class="max-h-48 overflow-y-auto px-1.5">
                  <li
                    v-for="u in users"
                    :key="u.name"
                    class="cursor-pointer rounded px-2.5 py-1.5 text-base text-ink-gray-7 hover:bg-surface-gray-3"
                    @click="selectUser(u)"
                  >
                    {{ u.full_name || u.name }}
                  </li>
                </ul>
              </div>
            </template>
          </Popover>
        </div>

        <!-- Section toggles -->
        <div v-if="selectedUser" class="flex flex-col gap-1">
          <div class="text-sm font-medium text-ink-gray-6 mb-1 px-1">{{ __('Разделы') }}</div>
          <div
            v-for="section in sections"
            :key="section.key"
            class="flex items-center justify-between rounded-lg px-3 py-2.5 hover:bg-surface-gray-1 transition-colors"
          >
            <span class="text-sm text-ink-gray-8">{{ section.label }}</span>
            <!-- Toggle switch -->
            <button
              type="button"
              class="relative inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full transition-colors duration-200"
              :class="isVisible(section.key) ? 'bg-blue-500' : 'bg-surface-gray-4'"
              @click="toggleSection(section.key)"
            >
              <span
                class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform duration-200"
                :class="isVisible(section.key) ? 'translate-x-4' : 'translate-x-0.5'"
              />
            </button>
          </div>
        </div>

        <div v-else class="py-8 text-center text-sm text-ink-gray-4">
          {{ __('Выберите пользователя для управления видимостью разделов') }}
        </div>
      </div>
    </template>
    <template v-if="selectedUser" #actions>
      <Button
        variant="solid"
        :label="__('Сохранить')"
        :loading="saving"
        @click="save"
      />
    </template>
  </Dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { call, toast, Dialog, FeatherIcon, Popover } from 'frappe-ui'
import { sessionStore } from '@/stores/session'
import { loadMyHiddenSections } from '@/stores/visibility'

const show = defineModel({ type: Boolean })

const { user: currentUser } = sessionStore()

const sections = [
  { key: 'Dashboard',  label: 'Панель инструментов' },
  { key: 'Leads',      label: 'Лиды' },
  { key: 'Deals',      label: 'Сделки' },
  { key: 'Contacts',   label: 'Контакты' },
  { key: 'Organizations', label: 'Организации' },
  { key: 'Warehouses', label: 'Склад' },
  { key: 'Debtors',    label: 'Дебиторы' },
  { key: 'RKO',        label: 'РКО' },
  { key: 'Presences',  label: 'Присутствия' },
  { key: 'Sales',      label: 'Продажи' },
  { key: 'Notes',      label: 'Заметки' },
  { key: 'Tasks',      label: 'Задачи' },
  { key: 'Calendar',   label: 'Календарь' },
  { key: 'Call Logs',  label: 'Журнал звонков' },
]

const users = ref([])
const selectedUser = ref('')
const showUserDropdown = ref(false)
const hiddenSet = ref(new Set())
const saving = ref(false)

const selectedUserLabel = computed(() => {
  if (!selectedUser.value) return ''
  const u = users.value.find((x) => x.name === selectedUser.value)
  return u ? (u.full_name || u.name) : selectedUser.value
})

onMounted(async () => {
  try {
    const list = await call('crm.integrations.visibility_api.get_all_users')
    users.value = list || []
  } catch {
    users.value = []
  }
})

async function selectUser(u) {
  selectedUser.value = u.name
  showUserDropdown.value = false
  try {
    const hidden = await call('crm.integrations.visibility_api.get_user_hidden_sections', {
      user: u.name,
    })
    hiddenSet.value = new Set(hidden || [])
  } catch {
    hiddenSet.value = new Set()
  }
}

function isVisible(key) {
  return !hiddenSet.value.has(key)
}

function toggleSection(key) {
  const next = new Set(hiddenSet.value)
  if (next.has(key)) {
    next.delete(key)
  } else {
    next.add(key)
  }
  hiddenSet.value = next
}

async function save() {
  saving.value = true
  try {
    await call('crm.integrations.visibility_api.set_user_hidden_sections', {
      user: selectedUser.value,
      hidden_sections: JSON.stringify([...hiddenSet.value]),
    })
    toast.success(__('Настройки видимости сохранены'))
    if (selectedUser.value === currentUser) {
      await loadMyHiddenSections()
    }
  } catch (err) {
    toast.error(err?.messages?.[0] || __('Не удалось сохранить настройки'))
  } finally {
    saving.value = false
  }
}
</script>

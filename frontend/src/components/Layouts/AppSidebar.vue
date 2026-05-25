<template>
  <div
    class="relative flex h-full flex-col justify-between transition-all duration-300 ease-in-out"
    :class="isSidebarCollapsed ? 'w-12' : 'w-[220px]'"
  >
    <div class="p-2">
      <UserDropdown :isCollapsed="isSidebarCollapsed" />
    </div>
    <div class="flex-1 overflow-y-auto">
      <div class="flex flex-col">
        <SidebarLink
          id="notifications-btn"
          :label="__('Notifications')"
          :icon="NotificationsIcon"
          :isCollapsed="isSidebarCollapsed"
          class="relative mx-2 my-[1.5px]"
          @click="() => toggleNotificationPanel()"
        >
          <template #right>
            <Badge
              v-if="!isSidebarCollapsed && unreadNotificationsCount"
              :label="unreadNotificationsCount"
              variant="subtle"
            />
            <div
              v-else-if="unreadNotificationsCount"
              class="absolute -left-1.5 top-1 z-20 h-[5px] w-[5px] translate-x-6 translate-y-1 rounded-full bg-surface-gray-6 ring-1 ring-white"
            />
          </template>
        </SidebarLink>
      </div>
      <div v-for="view in allViews" :key="view.label">
        <div class="mx-2 my-1.5" />
        <CollapsibleSection
          :label="view.name"
          :hideLabel="view.hideLabel"
          :opened="view.opened"
        >
          <template #header="{ opened, hide, toggle }">
            <div
              v-if="!hide"
              class="flex items-center cursor-pointer gap-1.5 text-base text-ink-gray-5 transition-all duration-300 ease-in-out"
              :class="
                isSidebarCollapsed
                  ? 'h-0 overflow-hidden opacity-0'
                  : 'px-4 pt-[11px] pb-2.5 w-auto opacity-100'
              "
              @click="toggle()"
            >
              <FeatherIcon
                name="chevron-right"
                class="h-4 text-ink-gray-9 transition-all duration-300 ease-in-out"
                :class="{ 'rotate-90': opened }"
              />
              <span>{{ __(view.name) }}</span>
            </div>
          </template>
          <nav class="flex flex-col">
            <SidebarLink
              v-for="link in view.views"
              :key="link.label"
              :icon="link.icon"
              :label="__(link.label)"
              :to="link.to"
              :isCollapsed="isSidebarCollapsed"
              class="mx-2 my-[1.5px]"
            />
          </nav>
        </CollapsibleSection>
      </div>
    </div>
    <div class="m-2 flex flex-col gap-1">
      <div class="flex flex-col gap-2 mb-1">
        <SignupBanner
          v-if="isDemoSite"
          :isSidebarCollapsed="isSidebarCollapsed"
          :afterSignup="() => capture('signup_from_demo_site')"
        />
        <TrialBanner
          v-if="isFCSite"
          :isSidebarCollapsed="isSidebarCollapsed"
          :afterUpgrade="() => capture('upgrade_plan_from_trial_banner')"
        />
      </div>
      <SidebarLink
        v-if="isManager() && isDemoDataCreated"
        class="text-ink-red-3 hover:bg-surface-red-2 focus:bg-surface-red-2"
        :label="__('Clear Demo Data')"
        :isCollapsed="isSidebarCollapsed"
        @click="() => clearDemoData()"
      >
        <template #icon>
          <BrushCleaningIcon class="h-4 w-4" />
        </template>
      </SidebarLink>
      <SidebarLink
        :label="isSidebarCollapsed ? __('Expand') : __('Collapse')"
        :isCollapsed="isSidebarCollapsed"
        class=""
        @click="isSidebarCollapsed = !isSidebarCollapsed"
      >
        <template #icon>
          <span class="grid h-4 w-4 flex-shrink-0 place-items-center">
            <CollapseSidebar
              class="h-4 w-4 text-ink-gray-7 duration-300 ease-in-out"
              :class="{ '[transform:rotateY(180deg)]': isSidebarCollapsed }"
            />
          </span>
        </template>
      </SidebarLink>
    </div>
    <Notifications />
    <Settings />
  </div>
</template>

<script setup>
import BrushCleaningIcon from '~icons/lucide/brush-cleaning'
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import PinIcon from '@/components/Icons/PinIcon.vue'
import UserDropdown from '@/components/UserDropdown.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import WarehousesIcon from '@/components/Icons/WarehousesIcon.vue'
import DebtorsIcon from '@/components/Icons/DebtorsIcon.vue'
import RKOIcon from '@/components/Icons/RKOIcon.vue'
import PresencesIcon from '@/components/Icons/PresencesIcon.vue'
import SalesIcon from '@/components/Icons/SalesIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CollapseSidebar from '@/components/Icons/CollapseSidebar.vue'
import NotificationsIcon from '@/components/Icons/NotificationsIcon.vue'
import HelpIcon from '@/components/Icons/HelpIcon.vue'
import SidebarLink from '@/components/SidebarLink.vue'
import Notifications from '@/components/Notifications.vue'
import Settings from '@/components/Settings/Settings.vue'
import { viewsStore } from '@/stores/views'
import { hiddenSections, loadMyHiddenSections } from '@/stores/visibility'
import {
  unreadNotificationsCount,
  notificationsStore,
} from '@/stores/notifications'
import { usersStore } from '@/stores/users'
import { sessionStore } from '@/stores/session'
import { showSettings, activeSettingsPage } from '@/composables/settings'
import { showChangePasswordModal } from '@/composables/modals'
import { useBroadcast } from '@/composables/useBroadcast.js'
import { FeatherIcon, call } from 'frappe-ui'
import {
  SignupBanner,
  TrialBanner,
  useTelemetry,
} from 'frappe-ui/frappe'
import router from '@/router'
import { useStorage } from '@vueuse/core'
import { useDemoData } from '@/composables/demoData'
import { ref, computed, onMounted } from 'vue'

const { getPinnedViews, getPublicViews } = viewsStore()
const { toggle: toggleNotificationPanel } = notificationsStore()
const { capture } = useTelemetry()
const { clearDemoData, isDemoDataCreated } = useDemoData()
const { send } = useBroadcast()

const isSidebarCollapsed = useStorage('isSidebarCollapsed', false)

const isFCSite = ref(window.is_fc_site)
const isDemoSite = ref(window.is_demo_site)

const links = [
  {
    label: 'Dashboard',
    icon: LucideLayoutDashboard,
    to: 'Dashboard',
  },
  {
    label: 'Leads',
    icon: LeadsIcon,
    to: 'Leads',
  },
  {
    label: 'Deals',
    icon: DealsIcon,
    to: 'Deals',
  },
  {
    label: 'Contacts',
    icon: ContactsIcon,
    to: 'Contacts',
  },
  {
    label: 'Organizations',
    icon: OrganizationsIcon,
    to: 'Organizations',
  },
  {
    label: 'Склад',
    icon: WarehousesIcon,
    to: 'Warehouses',
  },
  {
    label: 'Дебиторы',
    icon: DebtorsIcon,
    to: 'Debtors',
  },
  {
    label: 'РКО',
    icon: RKOIcon,
    to: 'RKO',
  },
  {
    label: 'Присутствия',
    icon: PresencesIcon,
    to: 'Presences',
  },
  {
    label: 'Продажи',
    icon: SalesIcon,
    to: 'Sales',
  },
  {
    label: 'Notes',
    icon: NoteIcon,
    to: 'Notes',
  },
  {
    label: 'Tasks',
    icon: TaskIcon,
    to: 'Tasks',
  },
  {
    label: 'Calendar',
    icon: CalendarIcon,
    to: 'Calendar',
  },
  {
    label: 'Call Logs',
    icon: PhoneIcon,
    to: 'Call Logs',
  },
]

const allViews = computed(() => {
  let _views = [
    {
      name: 'All Views',
      hideLabel: true,
      opened: true,
      views: links.filter((link) => {
        if (hiddenSections.value.has(link.to)) return false
        if (link.condition) return link.condition()
        return true
      }),
    },
  ]
  if (getPublicViews().length) {
    _views.push({
      name: 'Public Views',
      opened: true,
      views: parseView(getPublicViews()),
    })
  }

  if (getPinnedViews().length) {
    _views.push({
      name: 'Pinned Views',
      opened: true,
      views: parseView(getPinnedViews()),
    })
  }
  return _views
})

function parseView(views) {
  return views.map((view) => {
    return {
      label: view.label,
      icon: getIcon(view.route_name, view.icon),
      to: {
        name: view.route_name,
        params: { viewType: view.type || 'list' },
        query: { view: view.name },
      },
    }
  })
}

function getIcon(routeName, icon) {
  if (icon) return icon

  switch (routeName) {
    case 'Leads':
      return LeadsIcon
    case 'Deals':
      return DealsIcon
    case 'Contacts':
      return ContactsIcon
    case 'Organizations':
      return OrganizationsIcon
    case 'Warehouses':
      return WarehousesIcon
    case 'Debtors':
      return DebtorsIcon
    case 'RKO':
      return RKOIcon
    case 'Presences':
      return PresencesIcon
    case 'Sales':
      return SalesIcon
    case 'Notes':
      return NoteIcon
    case 'Call Logs':
      return PhoneIcon
    default:
      return PinIcon
  }
}

const { users, isManager } = usersStore()


onMounted(async () => {
  loadMyHiddenSections()
})

// help center
const articles = ref([
  {
    title: __('Introduction'),
    opened: false,
    subArticles: [
      { name: 'introduction', title: __('Introduction') },
      { name: 'setting-up', title: __('Setting Up') },
    ],
  },
  {
    title: __('Settings'),
    opened: false,
    subArticles: [
      { name: 'profile', title: __('Profile') },
      { name: 'custom-branding', title: __('Custom Branding') },
      { name: 'home-actions', title: __('Home Actions') },
      { name: 'invite-users', title: __('Invite Users') },
    ],
  },
  {
    title: __('Masters'),
    opened: false,
    subArticles: [
      { name: 'lead', title: __('Lead') },
      { name: 'deal', title: __('Deal') },
      { name: 'contact', title: __('Contact') },
      { name: 'organization', title: __('Organization') },
      { name: 'note', title: __('Note') },
      { name: 'task', title: __('Task') },
      { name: 'call-log', title: __('Call Log') },
      { name: 'email-template', title: __('Email Template') },
    ],
  },
  {
    title: __('Capturing Leads'),
    opened: false,
    subArticles: [{ name: 'web-form', title: __('Web Form') }],
  },
  {
    title: __('Views'),
    opened: false,
    subArticles: [
      { name: 'view', title: __('Saved View') },
      { name: 'public-view', title: __('Public View') },
      { name: 'pinned-view', title: __('Pinned View') },
    ],
  },
  {
    title: __('Other Features'),
    opened: false,
    subArticles: [
      { name: 'email-communication', title: __('Email Communication') },
      { name: 'comment', title: __('Comment') },
      { name: 'data', title: __('Data') },
      { name: 'service-level-agreement', title: __('Service Level Agreement') },
      { name: 'assignment-rule', title: __('Assignment Rule') },
      { name: 'notification', title: __('Notification') },
    ],
  },
  {
    title: __('Customization'),
    opened: false,
    subArticles: [
      { name: 'custom-fields', title: __('Custom Fields') },
      { name: 'custom-actions', title: __('Custom Actions') },
      { name: 'custom-statuses', title: __('Custom Statuses') },
      { name: 'custom-list-actions', title: __('Custom List Actions') },
      { name: 'quick-entry-layout', title: __('Quick Entry Layout') },
    ],
  },
  {
    title: __('Integration'),
    opened: false,
    subArticles: [
      { name: 'twilio', title: __('Twilio') },
      { name: 'exotel', title: __('Exotel') },
      { name: 'whatsapp', title: __('WhatsApp') },
      { name: 'erpnext', title: __('ERPNext') },
    ],
  },
  {
    title: __('Frappe CRM mobile'),
    opened: false,
    subArticles: [
      { name: 'mobile-app-installation', title: __('Mobile App Installation') },
    ],
  },
])
</script>

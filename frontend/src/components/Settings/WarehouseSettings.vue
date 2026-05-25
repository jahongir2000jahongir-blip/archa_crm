<template>
  <SettingsPage
    doctype="CRM 1C Settings"
    :options="{ afterSave: () => reloadSettings() }"
  />
</template>

<script setup>
import SettingsPage from 'frappe-ui/frappe'
import { ref } from 'vue'

const reloadSettings = () => {}
</script>

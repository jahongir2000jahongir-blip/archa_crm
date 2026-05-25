import { ref } from 'vue'
import { call } from 'frappe-ui'

export const hiddenSections = ref(new Set())

export async function loadMyHiddenSections() {
  try {
    const sections = await call('crm.integrations.visibility_api.get_my_hidden_sections')
    hiddenSections.value = new Set(sections || [])
  } catch {
    hiddenSections.value = new Set()
  }
}

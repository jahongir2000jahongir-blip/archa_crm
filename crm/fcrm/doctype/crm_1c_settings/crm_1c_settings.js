// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM 1C Settings", {
	refresh: function(frm) {
		frm.add_custom_button(__("Sync Now"), function() {
			frappe.call({
				method: "crm.integrations.one_c_sync.sync_from_1c",
				freeze: true,
				freeze_message: __("Syncing data from 1C..."),
				callback: function(r) {
					if (r.message) {
						frappe.msgprint(__("Sync completed successfully. {0} items synced.", [r.message.items_synced]));
						frm.reload_doc();
					}
				},
				error: function(r) {
					frappe.msgprint(__("Sync failed: {0}", [r.message]));
				}
			});
		}).addClass("btn-primary");
	},
});

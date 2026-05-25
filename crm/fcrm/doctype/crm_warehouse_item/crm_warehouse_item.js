// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM Warehouse Item", {
	refresh: function(frm) {
		frm.set_df_property("synced_from_1c", "read_only", 1);
	},
});

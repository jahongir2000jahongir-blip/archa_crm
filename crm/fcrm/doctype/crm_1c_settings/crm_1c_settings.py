# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRM1CSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		base_url: DF.Data
		category_mapping: DF.TableMultiSelect
		enabled: DF.Check
		last_sync: DF.Datetime | None
		password: DF.Password
		sync_frequency: DF.Literal["Every 15 minutes", "Every hour", "Manual"] | None
		total_items_synced: DF.Int
		username: DF.Data
	# end: auto-generated types

	def get_category_mapping(self):
		"""Return mapping dict: {source_category: target_category}"""
		mapping = {}
		for row in self.get("category_mapping"):
			if row.source_category and row.target_category:
				mapping[row.source_category.strip()] = row.target_category
		return mapping


def get_1c_connection():
	"""Get 1C API connection details."""
	settings = frappe.get_doc("CRM 1C Settings")
	if not settings.enabled:
		frappe.throw("1C Integration is not enabled. Please enable it in CRM 1C Settings.")
	if not settings.base_url or not settings.username or not settings.password:
		frappe.throw("Please configure 1C API URL, Username and Password in CRM 1C Settings.")

	return {
		"url": settings.base_url,
		"username": settings.username,
		"password": settings.get_password("password"),
	}


def setup_default_mapping():
	"""Set up default category mapping after migration."""
	from crm.integrations.one_c_sync import CATEGORY_MAPPING

	try:
		settings = frappe.get_doc("CRM 1C Settings")
	except frappe.DoesNotExistError:
		return

	if settings.get("category_mapping"):
		return

	for source, target in CATEGORY_MAPPING.items():
		settings.append("category_mapping", {
			"source_category": source,
			"target_category": target,
		})

	try:
		settings.save(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		pass

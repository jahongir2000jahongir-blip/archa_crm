# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMWarehouse(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		one_c_name: DF.Data | None
		address: DF.Link | None
		manager: DF.Link | None
		synced_from_1c: DF.Check
		warehouse_name: DF.Data
	# end: auto-generated types

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Склад",
				"type": "Data",
				"key": "warehouse_name",
				"width": "18rem",
			},
			{
				"label": "Наименование 1С",
				"type": "Data",
				"key": "one_c_name",
				"width": "14rem",
			},
			{
				"label": "Адрес",
				"type": "Link",
				"key": "address",
				"width": "12rem",
			},
			{
				"label": "Изменён",
				"type": "Datetime",
				"key": "modified",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"warehouse_name",
			"one_c_name",
			"address",
			"manager",
			"synced_from_1c",
			"modified",
		]
		return {"columns": columns, "rows": rows}

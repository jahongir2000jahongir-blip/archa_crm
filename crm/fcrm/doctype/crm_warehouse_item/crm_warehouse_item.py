# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMWarehouseItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		one_c_category: DF.Data | None
		article: DF.Data | None
		category: DF.Literal[
			"Краски", "Мебель", "Дверь", "Строительство", "Столы и стулья", "Спорттовар", "Электрика", "Прочее"
		] | None
		item_code: DF.Data
		item_name: DF.Data
		price: DF.Currency
		price_usd: DF.Currency
		quantity: DF.Float
		reserved: DF.Float
		synced_from_1c: DF.Check
		unit: DF.Data | None
		warehouse: DF.Link | None
		warehouse_name: DF.Data | None
	# end: auto-generated types

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Наименование",
				"type": "Data",
				"key": "item_name",
				"width": "4fr",
			},
			{
				"label": "Артикул",
				"type": "Data",
				"key": "article",
				"width": "2fr",
			},
			{
				"label": "Категория",
				"type": "Select",
				"key": "category",
				"width": "2fr",
			},
			{
				"label": "Склад",
				"type": "Link",
				"key": "warehouse",
				"width": "2fr",
			},
			{
				"label": "Количество",
				"type": "Int",
				"key": "quantity",
				"width": "1fr",
			},
		]
		rows = [
			"name",
			"item_code",
			"item_name",
			"article",
			"category",
			"warehouse",
			"warehouse_name",
			"quantity",
			"reserved",
			"unit",
			"price",
			"price_usd",
			"synced_from_1c",
			"one_c_category",
			"modified",
		]
		return {"columns": columns, "rows": rows}

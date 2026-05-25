# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMDebtor(Document):
	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		one_c_id: DF.Data
		contractor: DF.Data | None
		inn: DF.Data | None
		contract: DF.Data | None
		manager_id: DF.Data | None
		manager: DF.Data | None
		status: DF.Data | None
		debt_amount: DF.Currency | None
		debt_amount_usd: DF.Currency | None
		days_overdue: DF.Int | None
		payment_date: DF.Date | None
		last_payment_date: DF.Date | None
		comment: DF.Text | None
		synced_from_1c: DF.Check

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Контрагент",
				"type": "Data",
				"key": "contractor",
				"width": "3fr",
			},
			{
				"label": "Менеджер",
				"type": "Data",
				"key": "manager",
				"width": "2fr",
			},
			{
				"label": "Договор",
				"type": "Data",
				"key": "contract",
				"width": "2fr",
			},
			{
				"label": "Валюта",
				"type": "Data",
				"key": "currency",
				"width": "1fr",
			},
			{
				"label": "Сумма долга",
				"type": "Currency",
				"key": "debt_amount",
				"width": "2fr",
			},
			{
				"label": "Дней просрочки",
				"type": "Int",
				"key": "days_overdue",
				"width": "1fr",
			},
			{
				"label": "Статус",
				"type": "Data",
				"key": "status",
				"width": "1fr",
			},
			{
				"label": "Комментарий",
				"type": "Data",
				"key": "comment",
				"width": "3fr",
			},
		]
		rows = [
			"name",
			"one_c_id",
			"contractor",
			"inn",
			"contract",
			"manager_id",
			"manager",
			"currency",
			"status",
			"debt_amount",
			"debt_amount_usd",
			"days_overdue",
			"payment_date",
			"last_payment_date",
			"comment",
			"synced_from_1c",
			"modified",
		]
		return {"columns": columns, "rows": rows}

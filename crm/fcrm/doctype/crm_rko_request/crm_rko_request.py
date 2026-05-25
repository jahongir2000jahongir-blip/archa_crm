# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMRKORequest(Document):
	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		purpose: DF.Data
		amount: DF.Float | None
		expense_category: DF.Literal[
			"Материалы и сирье",
			"Зарплата / аванс",
			"Транспорт / топливо",
			"Аренда",
			"Коммунальные услуги",
			"Офисные расходы",
			"Ремонт и обслуживание",
			"Прочее",
		]
		recipient: DF.Data | None
		payment_date: DF.Date | None
		status: DF.Literal["На одобрении", "Одобрена", "Отклонена"]
		approver_role: DF.Literal["Главный бухгалтер", "Директор"] | None
		comment: DF.Text | None
		approver_comment: DF.Text | None
		redirect_comment: DF.Text | None
		approval_date: DF.Date | None

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Назначение платежа",
				"type": "Data",
				"key": "purpose",
				"width": "4fr",
			},
			{
				"label": "Заявитель",
				"type": "Data",
				"key": "created_by_name",
				"width": "2fr",
			},
			{
				"label": "Статья расходов",
				"type": "Select",
				"key": "expense_category",
				"width": "2fr",
			},
			{
				"label": "Сумма (сомони)",
				"type": "Float",
				"key": "amount",
				"width": "2fr",
			},
			{
				"label": "Дата создания",
				"type": "Date",
				"key": "payment_date",
				"width": "2fr",
			},
			{
				"label": "Статус",
				"type": "Select",
				"key": "status",
				"width": "2fr",
			},
			{
				"label": "На одобрение",
				"type": "Select",
				"key": "approver_role",
				"width": "2fr",
			},
			{
				"label": "Дата согласования",
				"type": "Date",
				"key": "approval_date",
				"width": "2fr",
			},
			{
				"label": "Комментарий",
				"type": "Text",
				"key": "approver_comment",
				"width": "3fr",
			},
		]
		rows = [
			"name",
			"purpose",
			"created_by_name",
			"amount",
			"expense_category",
			"recipient",
			"payment_date",
			"status",
			"approver_role",
			"comment",
			"approver_comment",
			"redirect_comment",
			"approval_date",
			"owner",
			"modified",
		]
		return {"columns": columns, "rows": rows}

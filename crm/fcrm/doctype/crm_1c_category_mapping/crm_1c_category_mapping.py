# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class CRM1CCategoryMapping(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		parent: DF.Data
		source_category: DF.Data
		target_category: DF.Literal[
			"Краски", "Мебель", "Дверь", "Строительство", "Столы и стулья", "Спорттовар", "Электрика", "Прочее"
		]
	# end: auto-generated types

	pass

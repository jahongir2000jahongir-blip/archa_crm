# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def get_user_approver_role() -> str | None:
	"""Return 'Главный бухгалтер', 'Директор', 'Кассир', or None for the current user."""
	roles = frappe.get_roles(frappe.session.user)
	if "Главный бухгалтер" in roles:
		return "Главный бухгалтер"
	if "Директор" in roles:
		return "Директор"
	if "Кассир" in roles:
		return "Кассир"
	return None


@frappe.whitelist()
def get_rko_counts() -> dict:
	"""Return tab counts for RKO requests."""
	user = frappe.session.user
	roles = frappe.get_roles(user)

	my_count = frappe.db.count("CRM RKO Request", {"owner": user})
	all_count = frappe.db.count("CRM RKO Request")

	if "Главный бухгалтер" in roles:
		pending_count = frappe.db.count(
			"CRM RKO Request",
			{"status": "На одобрении", "approver_role": "Главный бухгалтер"},
		)
	elif "Директор" in roles:
		pending_count = frappe.db.count(
			"CRM RKO Request",
			{"status": "На одобрении", "approver_role": "Директор"},
		)
	elif "Кассир" in roles:
		pending_count = frappe.db.count(
			"CRM RKO Request",
			{"status": "У кассира"},
		)
	else:
		pending_count = frappe.db.count(
			"CRM RKO Request",
			{"status": "На одобрении", "owner": user},
		)

	return {"my": my_count, "all": all_count, "pending": pending_count}


@frappe.whitelist()
def get_rko_request(name: str) -> dict:
	"""Return full details of a single RKO request."""
	doc = frappe.get_doc("CRM RKO Request", name)
	return doc.as_dict()


@frappe.whitelist()
def approve_rko_request(name: str) -> str:
	"""Approve an RKO request. Sets status to 'У кассира' and notifies Cashier."""
	roles = frappe.get_roles(frappe.session.user)
	doc = frappe.get_doc("CRM RKO Request", name)
	if doc.approver_role not in roles:
		frappe.throw("Нет прав для согласования этой заявки")
	approved_by_role = doc.approver_role
	doc.status = "У кассира"
	doc.approval_date = frappe.utils.today()
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	if approved_by_role == "Директор":
		_notify_approvers(doc, "Главный бухгалтер")
	_notify_approvers(doc, "Кассир")

	from crm.integrations.rko_external_api import send_rko_webhook
	user = frappe.session.user
	send_rko_webhook("rko_approved_to_cashier", {
		"name": doc.name,
		"purpose": doc.purpose,
		"amount": doc.amount,
		"approved_by": user,
		"approved_by_name": frappe.db.get_value("User", user, "full_name") or user,
		"approval_date": str(doc.approval_date),
	})

	try:
		from crm.integrations.telegram_bot import send_rko_notification
		send_rko_notification(doc.name, "Кассир")
	except Exception:
		frappe.log_error("Telegram notification failed", frappe.get_traceback())

	return doc.name


@frappe.whitelist()
def cashier_mark_paid_rko_request(name: str) -> str:
	"""Cashier marks request as paid. Sets final status to 'Оплачено'."""
	roles = frappe.get_roles(frappe.session.user)
	if "Кассир" not in roles:
		frappe.throw("Нет прав для отметки об оплате")
	doc = frappe.get_doc("CRM RKO Request", name)
	if doc.status != "У кассира":
		frappe.throw("Заявка не находится в статусе 'У кассира'")
	doc.status = "Оплачено"
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	from crm.integrations.rko_external_api import send_rko_webhook
	user = frappe.session.user
	send_rko_webhook("rko_paid", {
		"name": doc.name,
		"purpose": doc.purpose,
		"amount": doc.amount,
		"paid_by": user,
		"paid_by_name": frappe.db.get_value("User", user, "full_name") or user,
	})
	return doc.name


@frappe.whitelist()
def reject_rko_request(name: str, approver_comment: str) -> str:
	"""Reject an RKO request with a mandatory comment."""
	roles = frappe.get_roles(frappe.session.user)
	doc = frappe.get_doc("CRM RKO Request", name)
	if doc.approver_role not in roles:
		frappe.throw("Нет прав для отклонения этой заявки")
	doc.status = "Отклонена"
	doc.approver_comment = approver_comment
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	from crm.integrations.rko_external_api import send_rko_webhook
	user = frappe.session.user
	send_rko_webhook("rko_rejected", {
		"name": doc.name,
		"purpose": doc.purpose,
		"amount": doc.amount,
		"rejected_by": user,
		"rejected_by_name": frappe.db.get_value("User", user, "full_name") or user,
		"reason": approver_comment,
	})
	return doc.name


@frappe.whitelist()
def redirect_rko_request(name: str, redirect_comment: str) -> str:
	"""Redirect an RKO request to the other approver role."""
	roles = frappe.get_roles(frappe.session.user)
	doc = frappe.get_doc("CRM RKO Request", name)
	if doc.approver_role not in roles:
		frappe.throw("Нет прав для перенаправления этой заявки")

	new_role = "Директор" if doc.approver_role == "Главный бухгалтер" else "Главный бухгалтер"
	doc.approver_role = new_role
	doc.redirect_comment = redirect_comment
	doc.status = "На одобрении"
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	_notify_approvers(doc, new_role)

	try:
		from crm.integrations.telegram_bot import send_rko_notification
		send_rko_notification(doc.name, new_role)
	except Exception:
		frappe.log_error("Telegram notification failed", frappe.get_traceback())

	return doc.name


@frappe.whitelist()
def create_rko_request(
	purpose: str,
	amount: float | None = None,
	expense_category: str | None = None,
	recipient: str | None = None,
	payment_date: str | None = None,
	comment: str | None = None,
	approver_role: str | None = None,
) -> str:
	"""Create a new RKO Request."""
	role = approver_role or "Главный бухгалтер"
	doc = frappe.new_doc("CRM RKO Request")
	doc.purpose = purpose
	doc.amount = float(amount) if amount else 0
	doc.expense_category = expense_category or ""
	doc.recipient = recipient or ""
	doc.payment_date = payment_date
	doc.comment = comment or ""
	doc.approver_role = role
	doc.status = "На одобрении"
	doc.created_by_name = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
	doc.insert(ignore_permissions=False)
	frappe.db.commit()

	# Уведомляем нужных получателей в зависимости от выбранного согласующего
	notify_roles = ["Кассир"]
	if role == "Директор":
		notify_roles += ["Директор", "Главный бухгалтер"]
	else:
		notify_roles += ["Главный бухгалтер"]

	for r in notify_roles:
		_notify_approvers(doc, r)

	from crm.integrations.rko_external_api import send_rko_webhook
	creator_name = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
	send_rko_webhook("rko_created", {
		"name": doc.name,
		"purpose": doc.purpose,
		"amount": doc.amount,
		"expense_category": doc.expense_category,
		"recipient": doc.recipient,
		"payment_date": str(doc.payment_date) if doc.payment_date else None,
		"approver_role": doc.approver_role,
		"created_by": frappe.session.user,
		"created_by_name": creator_name,
		"comment": doc.comment,
	})

	try:
		from crm.integrations.telegram_bot import send_rko_notification
		send_rko_notification(doc.name, doc.approver_role)
	except Exception:
		frappe.log_error("Telegram notification failed", frappe.get_traceback())

	return doc.name


def _notify_approvers(doc, role: str):
	"""Send CRM notification to all users with the given approver role."""
	from crm.fcrm.doctype.crm_notification.crm_notification import notify_user

	approvers = frappe.get_all(
		"Has Role",
		fields=["parent"],
		filters={"role": role, "parenttype": "User"},
	)
	creator = frappe.session.user
	creator_name = frappe.db.get_value("User", creator, "full_name") or creator

	for approver in approvers:
		to_user = approver.parent
		if to_user in ("Guest",):
			continue
		notify_user({
			"owner": creator,
			"assigned_to": to_user,
			"notification_type": "Assignment",
			"message": f"Новая заявка РКО от {creator_name}",
			"notification_text": f"Назначение: {doc.purpose}",
			"reference_doctype": "CRM RKO Request",
			"reference_docname": doc.name,
			"redirect_to_doctype": "CRM RKO Request",
			"redirect_to_docname": doc.name,
		})

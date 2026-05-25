import json

import frappe


@frappe.whitelist()
def get_all_users() -> list:
	"""Return all enabled non-guest users for the visibility admin UI."""
	return frappe.get_all(
		"User",
		filters={"enabled": 1, "name": ["not in", ["Guest"]]},
		fields=["name", "full_name"],
		order_by="full_name asc",
	)


@frappe.whitelist()
def get_user_hidden_sections(user: str) -> list:
	"""Return the list of hidden section keys for the given user."""
	raw = frappe.db.get_value("CRM User Section Visibility", user, "hidden_sections")
	if not raw:
		return []
	try:
		return json.loads(raw)
	except Exception:
		return []


@frappe.whitelist()
def set_user_hidden_sections(user: str, hidden_sections: str) -> str:
	"""Save hidden sections (JSON array string) for the given user."""
	if frappe.db.exists("CRM User Section Visibility", user):
		frappe.db.set_value(
			"CRM User Section Visibility", user, "hidden_sections", hidden_sections
		)
	else:
		doc = frappe.new_doc("CRM User Section Visibility")
		doc.user = user
		doc.hidden_sections = hidden_sections
		doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return user


@frappe.whitelist()
def get_my_hidden_sections() -> list:
	"""Return hidden sections for the current session user."""
	return get_user_hidden_sections(frappe.session.user)

import frappe
import requests
from requests.auth import HTTPBasicAuth


def _fetch_1c_data():
	settings = frappe.get_doc("CRM 1C Settings")
	if not settings.enabled:
		frappe.throw("1C Integration is not enabled.")
	response = requests.post(
		settings.base_url,
		auth=HTTPBasicAuth(settings.username, settings.get_password("password")),
		headers={"Accept": "application/json", "Content-Type": "application/json"},
		json={},
		timeout=60,
	)
	response.raise_for_status()
	return response.json()


def _format_rows(items, extra_fields=None):
	result = []
	for item in items:
		row = {
			"shop": item.get("shop") or "—",
			"direction": item.get("direction") or "—",
			"manager": item.get("manager") or "—",
			"amount": item.get("amount") or 0,
			"amountUsd": item.get("amountUsd") or 0,
			"currency": item.get("currency") or "TJS",
		}
		if extra_fields:
			for f in extra_fields:
				row[f] = item.get(f)
		result.append(row)
	return result


@frappe.whitelist()
def get_sales_data():
	try:
		data = _fetch_1c_data()
		return {
			"day": _format_rows(data.get("salesDay", [])),
			"week": _format_rows(data.get("salesWeek", [])),
			"month": _format_rows(data.get("salesMonth", [])),
			"quarter": _format_rows(data.get("salesQuarter", [])),
			"year": _format_rows(data.get("salesYear", [])),
			"plan": _format_rows(data.get("Планы", []), extra_fields=["month", "year"]),
		}
	except Exception as e:
		frappe.log_error(str(e), "CRM Sales API")
		frappe.throw(str(e))

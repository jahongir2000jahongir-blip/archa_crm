# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json
from datetime import datetime

import frappe
import requests
from requests.auth import HTTPBasicAuth


CATEGORY_MAPPING = {
	"ДБ Рубеж": "Мебель",
	"PLATINUM": "Краски",
	"Sova": "Краски",
	"Арча Мебель": "Мебель",
	"ДБ Канадка": "Дверь",
	"ДБ МДФ": "Дверь",
	"ДБ ПМ": "Дверь",
	"ДБ Шпон": "Дверь",
	"Инвентарь и принадлежности": "Прочее",
	"КНР": "Прочее",
	"КФ Фортуна Ко": "Дверь",
	"Карниз": "Дверь",
	"Компютеры": "Прочее",
	"Лестница": "Строительство",
	"Материалы Продукции База ЦБ2": "Прочее",
	"Мебели Зебо люкс": "Мебель",
	"Мебель и принадлежности": "Мебель",
	"Наличники": "Дверь",
	"Оргтехника": "Дверь",
	"Петля": "Дверь",
	"Рекламные продукции": "Прочее",
	"Рынок": "Строительство",
	"Сандали": "Столы и стулья",
	"Силкоат": "Краски",
	"Узбекистан": "Мебель",
	"Фурнитура": "Прочее",
	"Хоз часть": "Прочее",
	"ЦБ-1": "Строительство",
	"ЦУМ Спорттовар": "Спорттовар",
	"замок": "Прочее",
}


def get_1c_settings():
	"""Get 1C integration settings."""
	return frappe.get_doc("CRM 1C Settings")


def fetch_data_from_1c():
	"""Fetch all data from 1C API."""
	settings = get_1c_settings()
	if not settings.enabled:
		frappe.throw("1C Integration is not enabled.")

	url = settings.base_url
	username = settings.username
	password = settings.get_password("password")

	try:
		response = requests.post(
			url,
			auth=HTTPBasicAuth(username, password),
			headers={"Accept": "application/json", "Content-Type": "application/json"},
			json={},
			timeout=60,
		)
		response.raise_for_status()
		return response.json()
	except requests.exceptions.ConnectionError as e:
		frappe.throw(f"Cannot connect to 1C API: {e}")
	except requests.exceptions.Timeout:
		frappe.throw("Connection to 1C API timed out.")
	except requests.exceptions.HTTPError as e:
		frappe.throw(f"1C API returned an error: {e}")


def get_category(category_1c):
	"""Map 1C category to CRM category."""
	category_1c = category_1c.strip() if category_1c else ""

	settings = get_1c_settings()
	db_mapping = settings.get_category_mapping()

	if category_1c in db_mapping:
		return db_mapping[category_1c]

	return CATEGORY_MAPPING.get(category_1c, "Прочее")


def get_or_create_warehouse(warehouse_1c_name):
	"""Get or create a CRM Warehouse record from 1C warehouse name."""
	if not warehouse_1c_name:
		return None

	warehouse_1c_name = warehouse_1c_name.strip()

	existing = frappe.db.exists("CRM Warehouse", {"one_c_name": warehouse_1c_name})
	if existing:
		return existing

	warehouses = frappe.get_all("CRM Warehouse", filters={"warehouse_name": warehouse_1c_name}, limit=1)
	if warehouses:
		wh = frappe.get_doc("CRM Warehouse", warehouses[0].name)
		wh.db_set("one_c_name", warehouse_1c_name, commit=True)
		return wh.name

	doc = frappe.new_doc("CRM Warehouse")
	doc.warehouse_name = warehouse_1c_name
	doc.one_c_name = warehouse_1c_name
	doc.synced_from_1c = 1
	doc.insert(ignore_permissions=True)
	return doc.name


def sync_warehouses_from_1c(data):
	"""Create/update warehouse records from 1C data."""
	warehouses_in_1c = set()
	for item in data.get("Остатки", []):
		wh_name = item.get("Склад", "").strip()
		if wh_name:
			warehouses_in_1c.add(wh_name)

	created_count = 0
	for wh_name in warehouses_in_1c:
		if not frappe.db.exists("CRM Warehouse", {"one_c_name": wh_name}):
			existing_by_name = frappe.db.exists("CRM Warehouse", {"warehouse_name": wh_name})
			if existing_by_name:
				doc = frappe.get_doc("CRM Warehouse", existing_by_name)
				doc.one_c_name = wh_name
				doc.synced_from_1c = 1
				doc.save(ignore_permissions=True)
			else:
				doc = frappe.new_doc("CRM Warehouse")
				doc.warehouse_name = wh_name
				doc.one_c_name = wh_name
				doc.synced_from_1c = 1
				doc.insert(ignore_permissions=True)
				created_count += 1

	return created_count


def sync_items_from_1c(data):
	"""Create/update warehouse items from 1C data."""
	items_data = data.get("Остатки", [])
	if not items_data:
		return 0

	items_synced = 0
	for item in items_data:
		item_code_1c = str(item.get("Код", "")).strip()
		article = item.get("Артикул", "").strip()
		item_name = item.get("Наименование", "").strip()
		category_1c = item.get("Категория", "").strip()
		quantity = int(float(item.get("Количество", 0) or 0))
		unit = item.get("ЕдИзм", "").strip()
		price = item.get("Цена", 0)
		price_usd = item.get("ЦенаUsd", 0)
		warehouse_1c_name = item.get("Склад", "").strip()
		reserved = item.get("Резерв", 0)

		if not item_name:
			continue

		category = get_category(category_1c)
		warehouse = get_or_create_warehouse(warehouse_1c_name)

		item_code = f"{item_code_1c}-{warehouse_1c_name}" if warehouse_1c_name else item_code_1c

		existing = frappe.db.exists("CRM Warehouse Item", {"item_code": item_code})
		if existing:
			doc = frappe.get_doc("CRM Warehouse Item", existing)
			doc.item_name = item_name
			doc.article = article
			doc.category = category
			doc.quantity = quantity
			doc.unit = unit
			doc.price = price
			doc.price_usd = price_usd
			doc.warehouse = warehouse
			doc.warehouse_name = warehouse_1c_name
			doc.reserved = reserved
			doc.synced_from_1c = 1
			doc.one_c_category = category_1c
			doc.save(ignore_permissions=True)
		else:
			doc = frappe.new_doc("CRM Warehouse Item")
			doc.item_code = item_code
			doc.item_name = item_name
			doc.article = article
			doc.category = category
			doc.quantity = quantity
			doc.unit = unit
			doc.price = price
			doc.price_usd = price_usd
			doc.warehouse = warehouse
			doc.warehouse_name = warehouse_1c_name
			doc.reserved = reserved
			doc.synced_from_1c = 1
			doc.one_c_category = category_1c
			doc.insert(ignore_permissions=True)

		items_synced += 1

	return items_synced


def update_sync_status(items_synced):
	"""Update last sync time and count in settings."""
	settings = get_1c_settings()
	settings.last_sync = datetime.now()
	settings.total_items_synced = items_synced
	settings.save(ignore_permissions=True)


def sync_debtors_from_1c(data):
	"""Create/update debtor records from 1C data."""
	debtors_data = data.get("Дебиторы", [])
	if not debtors_data:
		return 0

	def s(v): return (v or "").strip()

	synced = 0
	skipped = 0
	for item in debtors_data:
		one_c_id = str(item.get("id", "")).strip()
		if not one_c_id:
			continue

		try:
			contractor = s(item.get("Контрагент"))
			inn = s(item.get("ИНН"))
			contract = s(item.get("Договор"))
			manager_id = s(str(item.get("managerId") or ""))
			manager = s(item.get("Менеджер"))
			currency = s(item.get("Валюта"))
			comment = s(item.get("Комментарий"))
			debt_amount = item.get("СуммаДолга") or 0
			debt_amount_usd = item.get("СуммаДолгаUsd") or 0
			days_overdue = int(float(item.get("ДнейПросрочки") or 0))
			status = s(item.get("Статус"))

			payment_date_raw = item.get("ДатаОплаты", "")
			last_payment_date_raw = item.get("ДатаПоследнейОплаты", "")
			payment_date = _parse_date(payment_date_raw)
			last_payment_date = _parse_date(last_payment_date_raw)

			existing = frappe.db.exists("CRM Debtor", {"one_c_id": one_c_id})
			if existing:
				doc = frappe.get_doc("CRM Debtor", existing)
				doc.contractor = contractor
				doc.inn = inn
				doc.contract = contract
				doc.currency = currency
				doc.manager_id = manager_id
				doc.manager = manager
				doc.debt_amount = debt_amount
				doc.debt_amount_usd = debt_amount_usd
				doc.days_overdue = days_overdue
				doc.payment_date = payment_date
				doc.last_payment_date = last_payment_date
				doc.status = status
				doc.comment = comment
				doc.synced_from_1c = 1
				doc.save(ignore_permissions=True)
			else:
				doc = frappe.new_doc("CRM Debtor")
				doc.one_c_id = one_c_id
				doc.contractor = contractor
				doc.inn = inn
				doc.contract = contract
				doc.currency = currency
				doc.manager_id = manager_id
				doc.manager = manager
				doc.debt_amount = debt_amount
				doc.debt_amount_usd = debt_amount_usd
				doc.days_overdue = days_overdue
				doc.payment_date = payment_date
				doc.last_payment_date = last_payment_date
				doc.status = status
				doc.comment = comment
				doc.synced_from_1c = 1
				doc.insert(ignore_permissions=True)

			synced += 1
		except Exception as e:
			skipped += 1
			frappe.log_error(
				f"Failed to sync debtor id={one_c_id}: {e}",
				"CRM Debtor Sync",
			)

	return synced


def _parse_date(date_str):
	"""Parse date string from 1C, return None if empty/invalid."""
	if not date_str:
		return None
	try:
		from datetime import datetime as dt
		for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
			try:
				return dt.strptime(date_str.strip(), fmt).date()
			except ValueError:
				continue
	except Exception:
		pass
	return None


@frappe.whitelist()
def sync_from_1c():
	"""Main sync function: fetch data from 1C and create/update CRM records."""
	try:
		data = fetch_data_from_1c()

		warehouses_created = sync_warehouses_from_1c(data)
		frappe.db.commit()

		items_synced = sync_items_from_1c(data)
		frappe.db.commit()

		debtors_synced = sync_debtors_from_1c(data)
		frappe.db.commit()

		update_sync_status(items_synced)

		return {
			"success": True,
			"warehouses_created": warehouses_created,
			"items_synced": items_synced,
			"debtors_synced": debtors_synced,
			"last_sync": str(datetime.now()),
		}
	except Exception as e:
		frappe.log_error(f"1C Sync Error: {str(e)}", "CRM 1C Sync")
		frappe.throw(f"Sync failed: {str(e)}")


SALES_CACHE_KEY = "crm_1c_sales_data"
SALES_CACHE_TTL = 4 * 3600  # 4 hours


@frappe.whitelist(allow_guest=True)
def push_1c_data(token: str, data: str | dict) -> dict:
	"""
	Accept 1C data pushed from an external machine that has access to the 1C server.
	Runs warehouse/item/debtor sync and caches sales data.
	Auth: token must match rko_api_token in site_config.json.
	"""
	expected = frappe.conf.get("rko_api_token", "")
	if not expected or token != expected:
		frappe.throw("Неверный токен", frappe.AuthenticationError)

	if isinstance(data, str):
		data = json.loads(data)

	warehouses_created = sync_warehouses_from_1c(data)
	frappe.db.commit()

	items_synced = sync_items_from_1c(data)
	frappe.db.commit()

	debtors_synced = sync_debtors_from_1c(data)
	frappe.db.commit()

	update_sync_status(items_synced)

	sales_payload = {
		"day": data.get("salesDay", []),
		"week": data.get("salesWeek", []),
		"month": data.get("salesMonth", []),
		"quarter": data.get("salesQuarter", []),
		"year": data.get("salesYear", []),
		"plan": data.get("Планы", []),
		"history": data.get("salesHistory", []),
		"shops": data.get("shops", []),
		"currency": data.get("Курсы", {}),
		"cached_at": str(datetime.now()),
	}
	frappe.cache().set_value(SALES_CACHE_KEY, sales_payload, expires_in_sec=SALES_CACHE_TTL)

	return {
		"success": True,
		"warehouses_created": warehouses_created,
		"items_synced": items_synced,
		"debtors_synced": debtors_synced,
		"last_sync": str(datetime.now()),
	}


@frappe.whitelist()
def get_debtor_stats():
	"""Return summary stats for debtors dashboard."""
	all_debtors = frappe.db.get_all(
		"CRM Debtor",
		fields=["debt_amount", "days_overdue", "comment"],
	)

	total_debt = sum(d.get("debt_amount") or 0 for d in all_debtors)
	overdue_count = sum(1 for d in all_debtors if (d.get("days_overdue") or 0) > 0)
	critical_count = sum(1 for d in all_debtors if (d.get("days_overdue") or 0) > 30)
	no_comment_count = sum(1 for d in all_debtors if not (d.get("comment") or "").strip())

	return {
		"total_debt": total_debt,
		"overdue_count": overdue_count,
		"critical_count": critical_count,
		"no_comment_count": no_comment_count,
		"total_count": len(all_debtors),
	}


@frappe.whitelist()
def get_debtor_filter_options():
	"""Return distinct contractors, managers, and statuses for filter dropdowns."""
	def get_distinct(field):
		rows = frappe.db.get_all(
			"CRM Debtor",
			fields=[field],
			filters={field: ["!=", ""]},
			distinct=True,
			order_by=field,
		)
		return sorted({r[field] for r in rows if r[field]})

	return {
		"contractors": get_distinct("contractor"),
		"managers": get_distinct("manager"),
		"statuses": get_distinct("status"),
	}


@frappe.whitelist()
def get_warehouse_item_counts():
	"""Get item counts per category for tab display."""
	all_items = frappe.db.count("CRM Warehouse Item")
	counts = {"All": all_items}

	categories = [
		"Краски", "Мебель", "Дверь", "Строительство",
		"Столы и стулья", "Спорттовар", "Электрика", "Прочее"
	]

	for cat in categories:
		count = frappe.db.count("CRM Warehouse Item", {"category": cat})
		counts[cat] = count

	return counts

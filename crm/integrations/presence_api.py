import json
import frappe


CACHE_KEY = "crm_presence_statuses"
VALID_STATUSES = ("В офисе", "Не в офисе")

# Mapping from mobile app status values to CRM display values
_STATUS_MAP = {
    "in_office": "В офисе",
    "not_in_office": "Не в офисе",
}


def _verify_token(token: str):
    expected = frappe.conf.get("rko_api_token", "")
    if not expected:
        frappe.throw("rko_api_token не настроен в site_config.json", frappe.AuthenticationError)
    if token != expected:
        frappe.throw("Неверный API токен", frappe.AuthenticationError)


def _get_statuses() -> dict:
    return frappe.cache().get_value(CACHE_KEY) or {}


def _set_statuses(statuses: dict):
    frappe.cache().set_value(CACHE_KEY, statuses)


@frappe.whitelist()
def get_presences() -> list:
    """Return all CRM users with their presence status."""
    crm_roles = [
        "Пользователь", "Sales User", "Sales Manager",
        "Директор", "Главный бухгалтер", "Кассир",
    ]
    has_role = frappe.get_all(
        "Has Role",
        fields=["parent"],
        filters={"role": ["in", crm_roles], "parenttype": "User"},
    )
    emails = list({r.parent for r in has_role if r.parent not in ("Administrator", "Guest")})

    if not emails:
        return []

    users = frappe.get_all(
        "User",
        fields=["name", "full_name", "user_image"],
        filters={"name": ["in", emails], "enabled": 1},
        order_by="full_name asc",
    )

    statuses = _get_statuses()
    return [
        {
            "email": u.name,
            "full_name": u.full_name or u.name,
            "user_image": u.user_image,
            "status": statuses.get(u.name, "Не в офисе"),
        }
        for u in users
    ]


@frappe.whitelist(allow_guest=True)
def update_presence(user_email: str, status: str, token: str) -> dict:
    """Update presence status for a single user. Called by external system."""
    _verify_token(token)
    if status not in VALID_STATUSES:
        frappe.throw(f"Недопустимый статус. Допустимые: {VALID_STATUSES}")

    statuses = _get_statuses()
    statuses[user_email] = status
    _set_statuses(statuses)

    frappe.publish_realtime("presence_updated", {"email": user_email, "status": status})
    return {"success": True, "email": user_email, "status": status}


@frappe.whitelist(allow_guest=True)
def mobile_update_presence() -> dict:
	"""
	Endpoint for mobile app. Accepts JSON body:
	{
	  "login": "user@example.com",
	  "status": "in_office" | "not_in_office",
	  "timestamp": "2026-05-24T09:30:00.000",
	  "latitude": 38.57,
	  "longitude": 68.79,
	  "distance_meters": 12.3
	}
	Auth: token via ?token=... query param or X-Api-Token header.
	"""
	token = (
		frappe.form_dict.get("token")
		or frappe.get_request_header("X-Api-Token")
		or frappe.get_request_header("Authorization", "").removeprefix("Bearer ").strip()
	)
	_verify_token(token)

	try:
		body = json.loads(frappe.request.data)
	except Exception:
		frappe.throw("Неверный JSON", frappe.ValidationError)

	login = body.get("login", "").strip().lower()
	mobile_status = body.get("status", "")
	timestamp = body.get("timestamp")
	latitude = body.get("latitude")
	longitude = body.get("longitude")
	distance_meters = body.get("distance_meters")

	if not login:
		frappe.throw("Поле 'login' обязательно", frappe.ValidationError)

	crm_status = _STATUS_MAP.get(mobile_status)
	if not crm_status:
		frappe.throw(
			f"Неизвестный статус '{mobile_status}'. Допустимые: {list(_STATUS_MAP.keys())}",
			frappe.ValidationError,
		)

	# Check that the user exists in Frappe
	user_exists = frappe.db.exists("User", {"name": login, "enabled": 1})
	if not user_exists:
		frappe.throw(f"Пользователь '{login}' не найден", frappe.DoesNotExistError)

	statuses = _get_statuses()
	statuses[login] = crm_status
	_set_statuses(statuses)

	frappe.publish_realtime("presence_updated", {
		"email": login,
		"status": crm_status,
		"timestamp": timestamp,
		"latitude": latitude,
		"longitude": longitude,
		"distance_meters": distance_meters,
	})

	return {
		"success": True,
		"login": login,
		"status": crm_status,
		"timestamp": timestamp,
	}


@frappe.whitelist(allow_guest=True)
def bulk_update_presences(presences: str | list, token: str) -> dict:
    """
    Bulk update presence statuses.
    presences: JSON list of {"email": "...", "status": "..."}
    """
    _verify_token(token)

    if isinstance(presences, str):
        import json
        presences = json.loads(presences)

    statuses = _get_statuses()
    updated = 0
    for item in presences:
        email = item.get("email") or item.get("user_email")
        status = item.get("status")
        if email and status in VALID_STATUSES:
            statuses[email] = status
            updated += 1

    _set_statuses(statuses)
    frappe.publish_realtime("presences_bulk_updated", {"statuses": statuses})
    return {"success": True, "updated": updated}

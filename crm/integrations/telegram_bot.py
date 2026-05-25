import json
import frappe
import requests

_TG_URL = "https://api.telegram.org/bot{token}/{method}"


def _tg(method, token, **payload):
	"""Call Telegram Bot API. Returns parsed JSON response."""
	url = _TG_URL.format(token=token, method=method)
	try:
		r = requests.post(url, json=payload, timeout=10)
		return r.json()
	except Exception:
		frappe.log_error("Telegram API call failed", frappe.get_traceback())
		return {}


def _format_rko_message(doc, header="📋 *Новая заявка РКО*"):
	lines = [f"{header} — {doc.name}", ""]
	lines.append(f"👤 Заявитель: {doc.created_by_name or ''}")
	lines.append(f"📝 Назначение: {doc.purpose or ''}")
	if doc.amount:
		lines.append(f"💰 Сумма: {doc.amount:,.2f} сомони")
	if doc.expense_category:
		lines.append(f"📂 Статья расходов: {doc.expense_category}")
	if doc.recipient:
		lines.append(f"🏢 Получатель: {doc.recipient}")
	if doc.payment_date:
		lines.append(f"📅 Дата: {doc.payment_date}")
	if doc.comment:
		lines.append(f"💬 Комментарий: {doc.comment}")
	return "\n".join(lines)


def _approval_keyboard(rko_name, approver_role):
	other = "Директор" if approver_role == "Главный бухгалтер" else "Главный бухгалтер"
	return {
		"inline_keyboard": [
			[
				{"text": "✅ Согласовать", "callback_data": f"a:{rko_name}"},
				{"text": "❌ Отклонить", "callback_data": f"r:{rko_name}"},
			],
			[
				{"text": f"🔄 Перенаправить → {other}", "callback_data": f"d:{rko_name}"},
			],
		]
	}


def _cashier_keyboard(rko_name):
	return {
		"inline_keyboard": [
			[{"text": "💵 Оплачено", "callback_data": f"p:{rko_name}"}]
		]
	}


def send_rko_notification(rko_name, approver_role):
	"""Send Telegram notification to the approver role about an RKO request."""
	token = frappe.conf.get("telegram_bot_token")
	if not token:
		return
	chat_ids = frappe.conf.get("telegram_chat_ids") or {}
	chat_id = chat_ids.get(approver_role)
	if not chat_id:
		return

	doc = frappe.get_doc("CRM RKO Request", rko_name)
	text = _format_rko_message(doc)

	if approver_role == "Кассир":
		keyboard = _cashier_keyboard(rko_name)
	else:
		keyboard = _approval_keyboard(rko_name, approver_role)

	resp = _tg("sendMessage", token,
		chat_id=chat_id,
		text=text,
		parse_mode="Markdown",
		reply_markup=keyboard,
	)

	msg_id = resp.get("result", {}).get("message_id")
	if msg_id:
		frappe.cache().set_value(
			f"tg_msg:{rko_name}:{chat_id}", msg_id, expires_in_sec=7 * 24 * 3600
		)


def _edit_rko_message(rko_name, chat_id, text):
	"""Edit a previously sent RKO notification message."""
	token = frappe.conf.get("telegram_bot_token")
	if not token:
		return
	msg_id = frappe.cache().get_value(f"tg_msg:{rko_name}:{chat_id}")
	if not msg_id:
		return
	_tg("editMessageText", token,
		chat_id=chat_id,
		message_id=msg_id,
		text=text,
		parse_mode="Markdown",
	)


def _get_user_for_role(role):
	"""Return email of first Frappe user with the given role (skip Guest/Administrator)."""
	rows = frappe.get_all(
		"Has Role", fields=["parent"],
		filters={"role": role, "parenttype": "User"},
	)
	for r in rows:
		if r.parent not in ("Guest", "Administrator"):
			return r.parent
	return None


def _get_role_for_chat_id(chat_id):
	"""Return (role, user_email) matching the given Telegram chat_id."""
	chat_ids = frappe.conf.get("telegram_chat_ids") or {}
	for role, cid in chat_ids.items():
		if str(cid) == str(chat_id):
			return role, _get_user_for_role(role)
	return None, None


@frappe.whitelist(allow_guest=True)
def handle_webhook():
	"""Telegram webhook endpoint. Receives updates and routes to action handlers."""
	secret = frappe.get_request_header("X-Telegram-Bot-Api-Secret-Token")
	expected = frappe.conf.get("rko_api_token")
	if expected and secret != expected:
		frappe.response["http_status_code"] = 403
		return "Forbidden"

	try:
		body = json.loads(frappe.request.data)
	except Exception:
		return "ok"

	if "callback_query" in body:
		_process_callback(body["callback_query"])
	elif "message" in body:
		msg = body["message"]
		chat_id = str(msg.get("chat", {}).get("id", ""))
		pending_key = f"tg_pending_reject:{chat_id}"
		pending = frappe.cache().get_value(pending_key)
		if pending:
			_finish_rejection(msg, pending, pending_key)

	return "ok"


def _process_callback(cb):
	token = frappe.conf.get("telegram_bot_token")
	if not token:
		return

	callback_id = cb.get("id")
	chat_id = str(cb.get("from", {}).get("id", ""))
	data = cb.get("data", "")

	if ":" not in data:
		return
	action, rko_name = data.split(":", 1)

	role, user_email = _get_role_for_chat_id(chat_id)
	if not user_email:
		_tg("answerCallbackQuery", token, callback_query_id=callback_id, text="⚠️ Нет прав")
		return

	from crm.integrations import rko_api

	prev_user = frappe.session.user
	try:
		frappe.set_user(user_email)

		if action == "a":
			rko_api.approve_rko_request(rko_name)
			_tg("answerCallbackQuery", token, callback_query_id=callback_id, text="✅ Согласовано")
			doc = frappe.get_doc("CRM RKO Request", rko_name)
			_edit_rko_message(
				rko_name, chat_id,
				f"✅ *Согласовано*\n\n{_format_rko_message(doc, header='📋 Заявка РКО')}",
			)

		elif action == "r":
			pending_key = f"tg_pending_reject:{chat_id}"
			frappe.cache().set_value(
				pending_key,
				{"rko_name": rko_name, "user_email": user_email, "chat_id": chat_id},
				expires_in_sec=600,
			)
			_tg("answerCallbackQuery", token, callback_query_id=callback_id, text="Введите причину")
			_tg("sendMessage", token,
				chat_id=int(chat_id),
				text="✏️ Введите причину отклонения заявки:",
			)

		elif action == "d":
			rko_api.redirect_rko_request(rko_name, redirect_comment="Перенаправлено через Telegram")
			doc = frappe.get_doc("CRM RKO Request", rko_name)
			new_role = doc.approver_role
			_tg("answerCallbackQuery", token, callback_query_id=callback_id,
				text=f"🔄 Перенаправлено → {new_role}")
			_edit_rko_message(
				rko_name, chat_id,
				f"🔄 *Перенаправлено → {new_role}*\n\n{_format_rko_message(doc, header='📋 Заявка РКО')}",
			)

		elif action == "p":
			rko_api.cashier_mark_paid_rko_request(rko_name)
			_tg("answerCallbackQuery", token, callback_query_id=callback_id, text="💵 Оплачено")
			doc = frappe.get_doc("CRM RKO Request", rko_name)
			_edit_rko_message(
				rko_name, chat_id,
				f"💵 *Оплачено*\n\n{_format_rko_message(doc, header='📋 Заявка РКО')}",
			)

	except Exception:
		frappe.log_error("Telegram callback error", frappe.get_traceback())
		_tg("answerCallbackQuery", token, callback_query_id=callback_id,
			text="⚠️ Ошибка. Проверьте CRM.")
	finally:
		frappe.set_user(prev_user)


def _finish_rejection(msg, pending, pending_key):
	"""Apply rejection with the text the approver sent after pressing Отклонить."""
	token = frappe.conf.get("telegram_bot_token")
	if not token:
		return

	chat_id = str(msg.get("chat", {}).get("id", ""))
	comment = msg.get("text", "").strip()
	rko_name = pending["rko_name"]
	user_email = pending["user_email"]

	frappe.cache().delete_value(pending_key)

	from crm.integrations import rko_api

	prev_user = frappe.session.user
	try:
		frappe.set_user(user_email)
		rko_api.reject_rko_request(rko_name, approver_comment=comment)
		doc = frappe.get_doc("CRM RKO Request", rko_name)
		_edit_rko_message(
			rko_name, chat_id,
			f"❌ *Отклонено*\n\n{_format_rko_message(doc, header='📋 Заявка РКО')}\n\n🚫 Причина: {comment}",
		)
		_tg("sendMessage", token, chat_id=int(chat_id), text=f"❌ Заявка {rko_name} отклонена.")
	except Exception:
		frappe.log_error("Telegram rejection error", frappe.get_traceback())
		_tg("sendMessage", token, chat_id=int(chat_id),
			text="⚠️ Ошибка при отклонении. Проверьте CRM.")
	finally:
		frappe.set_user(prev_user)


@frappe.whitelist()
def setup_webhook(site_url):
	"""Register Frappe as Telegram webhook receiver. Run once after deployment."""
	token = frappe.conf.get("telegram_bot_token")
	if not token:
		frappe.throw("telegram_bot_token не задан в site_config.json")
	url = f"{site_url.rstrip('/')}/api/method/crm.integrations.telegram_bot.handle_webhook"
	secret = frappe.conf.get("rko_api_token") or ""
	resp = _tg("setWebhook", token,
		url=url,
		secret_token=secret,
		allowed_updates=["callback_query", "message"],
	)
	return resp

# External API for Telegram bot integration with RKO requests.
# Authentication: pass api_token in every request.
# Store in site_config.json:
#   "rko_api_token": "<your-secret-token>"
#   "rko_webhook_url": "https://your-bot-server/webhook"

import frappe
import requests as http


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _verify_token(token: str):
    expected = frappe.conf.get("rko_api_token", "")
    if not expected:
        frappe.throw("rko_api_token не настроен в site_config.json", frappe.AuthenticationError)
    if token != expected:
        frappe.throw("Неверный API токен", frappe.AuthenticationError)


def send_rko_webhook(event: str, payload: dict):
    """POST event payload to the configured bot webhook URL. Never raises."""
    url = frappe.conf.get("rko_webhook_url", "")
    if not url:
        return
    try:
        payload["event"] = event
        http.post(url, json=payload, timeout=5)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Bot → CRM endpoints
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def approve_rko(name: str, user: str, token: str) -> dict:
    """
    Approve an RKO request on behalf of a CRM user.

    Called by the Telegram bot when Director or Chief Accountant taps "Approve".
    Sets status → 'У кассира' and notifies the Cashier.

    Args:
        name:  RKO request name, e.g. "CRM-RKO-0001"
        user:  CRM login (email) of the approver, e.g. "bakhrom@crm.local"
        token: shared secret from site_config.json → rko_api_token
    """
    _verify_token(token)

    doc = frappe.get_doc("CRM RKO Request", name)
    user_roles = frappe.get_roles(user)

    if doc.status != "На одобрении":
        frappe.throw(f"Заявка {name} не в статусе 'На одобрении'")
    if doc.approver_role not in user_roles:
        frappe.throw(f"Пользователь {user} не имеет роли '{doc.approver_role}'")

    approved_by_role = doc.approver_role
    doc.status = "У кассира"
    doc.approval_date = frappe.utils.today()
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    from crm.integrations.rko_api import _notify_approvers
    if approved_by_role == "Директор":
        _notify_approvers(doc, "Главный бухгалтер")
    _notify_approvers(doc, "Кассир")

    approver_name = frappe.db.get_value("User", user, "full_name") or user
    send_rko_webhook("rko_approved_to_cashier", {
        "name": doc.name,
        "purpose": doc.purpose,
        "amount": doc.amount,
        "approved_by": user,
        "approved_by_name": approver_name,
        "approval_date": str(doc.approval_date),
    })
    frappe.publish_realtime("rko_updated", {"name": doc.name, "status": doc.status})
    return {"success": True, "name": doc.name, "status": doc.status}


@frappe.whitelist(allow_guest=True)
def reject_rko(name: str, user: str, token: str, approver_comment: str = "") -> dict:
    """
    Reject an RKO request on behalf of a CRM user.

    Args:
        name:             RKO request name
        user:             CRM login of the approver
        token:            shared secret
        approver_comment: reason for rejection (required by business logic)
    """
    _verify_token(token)

    doc = frappe.get_doc("CRM RKO Request", name)
    user_roles = frappe.get_roles(user)

    if doc.status != "На одобрении":
        frappe.throw(f"Заявка {name} не в статусе 'На одобрении'")
    if doc.approver_role not in user_roles:
        frappe.throw(f"Пользователь {user} не имеет роли '{doc.approver_role}'")

    doc.status = "Отклонена"
    doc.approver_comment = approver_comment
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    approver_name = frappe.db.get_value("User", user, "full_name") or user
    send_rko_webhook("rko_rejected", {
        "name": doc.name,
        "purpose": doc.purpose,
        "amount": doc.amount,
        "rejected_by": user,
        "rejected_by_name": approver_name,
        "reason": approver_comment,
    })
    frappe.publish_realtime("rko_updated", {"name": doc.name, "status": doc.status})
    return {"success": True, "name": doc.name, "status": doc.status}


@frappe.whitelist(allow_guest=True)
def mark_paid_rko(name: str, user: str, token: str) -> dict:
    """Cashier marks request as paid (status → 'Оплачено')."""
    _verify_token(token)

    user_roles = frappe.get_roles(user)
    if "Кассир" not in user_roles:
        frappe.throw(f"Пользователь {user} не имеет роли 'Кассир'")

    doc = frappe.get_doc("CRM RKO Request", name)
    if doc.status != "У кассира":
        frappe.throw(f"Заявка {name} не в статусе 'У кассира'")

    doc.status = "Оплачено"
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    paid_by_name = frappe.db.get_value("User", user, "full_name") or user
    send_rko_webhook("rko_paid", {
        "name": doc.name,
        "purpose": doc.purpose,
        "amount": doc.amount,
        "paid_by": user,
        "paid_by_name": paid_by_name,
    })
    frappe.publish_realtime("rko_updated", {"name": doc.name, "status": doc.status})
    return {"success": True, "name": doc.name, "status": doc.status}


@frappe.whitelist(allow_guest=True)
def redirect_rko(name: str, user: str, token: str, redirect_comment: str = "") -> dict:
    """
    Redirect an RKO request to the other approver role.

    Toggles approver_role between Директор ↔ Главный бухгалтер,
    notifies all three roles and syncs to the website in real time.

    Args:
        name:             RKO request name
        user:             CRM login of the current approver
        token:            shared secret
        redirect_comment: reason for redirection
    """
    _verify_token(token)

    doc = frappe.get_doc("CRM RKO Request", name)
    user_roles = frappe.get_roles(user)

    if doc.status != "На одобрении":
        frappe.throw(f"Заявка {name} не в статусе 'На одобрении'")
    if doc.approver_role not in user_roles:
        frappe.throw(f"Пользователь {user} не имеет роли '{doc.approver_role}'")

    new_role = "Директор" if doc.approver_role == "Главный бухгалтер" else "Главный бухгалтер"
    doc.approver_role = new_role
    doc.redirect_comment = redirect_comment
    doc.status = "На одобрении"
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    from crm.integrations.rko_api import _notify_approvers
    _notify_approvers(doc, new_role)

    approver_name = frappe.db.get_value("User", user, "full_name") or user
    send_rko_webhook("rko_redirected", {
        "name": doc.name,
        "purpose": doc.purpose,
        "amount": doc.amount,
        "redirected_by": user,
        "redirected_by_name": approver_name,
        "new_approver_role": new_role,
        "redirect_comment": redirect_comment,
    })
    frappe.publish_realtime("rko_updated", {"name": doc.name, "status": doc.status})
    return {"success": True, "name": doc.name, "status": doc.status, "new_approver_role": new_role}


@frappe.whitelist(allow_guest=True)
def get_rko(name: str, token: str) -> dict:
    """Return full details of a single RKO request."""
    _verify_token(token)
    doc = frappe.get_doc("CRM RKO Request", name)
    return {
        "name": doc.name,
        "purpose": doc.purpose,
        "amount": doc.amount,
        "expense_category": doc.expense_category,
        "recipient": doc.recipient,
        "payment_date": str(doc.payment_date) if doc.payment_date else None,
        "status": doc.status,
        "approver_role": doc.approver_role,
        "approval_date": str(doc.approval_date) if doc.approval_date else None,
        "comment": doc.comment,
        "approver_comment": doc.approver_comment,
        "created_by": doc.owner,
        "created_by_name": frappe.db.get_value("User", doc.owner, "full_name") or doc.owner,
    }

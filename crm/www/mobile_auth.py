import frappe

no_cache = 1
no_sitemap = 1


def get_context(context):
	login = frappe.form_dict.get("login", "").strip()
	password = frappe.form_dict.get("password", "").strip()

	if login and password:
		try:
			from frappe.auth import LoginManager
			lm = LoginManager()
			lm.authenticate(user=login, pwd=password)
			lm.post_login()
		except frappe.AuthenticationError:
			pass
		except Exception:
			frappe.log_error("Mobile auth error", frappe.get_traceback())

	frappe.local.flags.redirect_location = "/crm"
	raise frappe.Redirect

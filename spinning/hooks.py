# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "spinning"
app_title = "Spinning"
app_publisher = "FinByz Tech Pvt Ltd"
app_description = "Custom app for spinning app"
app_icon = "/public/files/cone-yarn.png"
app_color = "Orange"
app_email = "info@finbyz.com"
app_license = "GPL 3.0"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/spinning/css/spinning.css"
# app_include_js = "/assets/spinning/js/spinning.js"

app_include_js = [
	"/assets/spinning/js/report_actions.js"
]

# include js, css files in header of web template
# web_include_css = "/assets/spinning/css/spinning.css"
# web_include_js = "/assets/spinning/js/spinning.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

doctype_js = {
	"Purchase Receipt": "public/js/doctype_js/purchase_receipt.js",
	"Purchase Invoice": "public/js/doctype_js/purchase_invoice.js",
	"Sales Invoice": "public/js/doctype_js/sales_invoice.js",
	"Delivery Note": "public/js/doctype_js/delivery_note.js",
	"Stock Reconciliation": "public/js/doctype_js/stock_reconciliation.js",
	"Purchase Order": "public/js/doctype_js/purchase_order.js",
	"Quality Inspection": "public/js/doctype_js/quality_inspection.js",
	"Quality Inspection Template": "public/js/doctype_js/quality_inspection_template.js"

}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "spinning.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "spinning.install.before_install"
# after_install = "spinning.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "spinning.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"spinning.tasks.all"
# 	],
# 	"daily": [
# 		"spinning.tasks.daily"
# 	],
# 	"hourly": [
# 		"spinning.tasks.hourly"
# 	],
# 	"weekly": [
# 		"spinning.tasks.weekly"
# 	]
# 	"monthly": [
# 		"spinning.tasks.monthly"
# 	]
# }

doc_events = {
	"Stock Entry": {
		"validate": "spinning.doc_events.stock_entry.validate",
		'before_save': "spinning.doc_events.stock_entry.before_save",
	},

	"Batch": {
		'before_naming': "spinning.doc_events.batch.before_naming",
	},

	"Purchase Receipt": {
		"validate": "spinning.doc_events.purchase_receipt.validate",
		"on_submit": "spinning.doc_events.purchase_receipt.on_submit",
		"on_cancel": "spinning.doc_events.purchase_receipt.on_cancel",
		"before_save": "spinning.doc_events.purchase_receipt.before_save",
	},
	
	"Purchase Invoice": {
		"validate": "spinning.doc_events.purchase_invoice.validate",
		"on_submit": "spinning.doc_events.purchase_invoice.on_submit"
	},

	"BOM": {
		"before_naming": "spinning.doc_events.bom.before_naming",
		"validate": "spinning.controllers.merge_validation.validate_merge",
		"on_submit":  "spinning.doc_events.bom.on_submit",
	},

	"Delivery Note": {
		"before_validate": "spinning.doc_events.delivery_note.before_validate",
		"before_save": "spinning.doc_events.delivery_note.before_save",
		"on_submit": "spinning.doc_events.delivery_note.on_submit",
		"on_cancel": "spinning.doc_events.delivery_note.on_cancel",
	},

	"Work Order": {
		"validate": "spinning.controllers.merge_validation.validate_merge",
		"before_save": "spinning.doc_events.work_order.before_save",
		"on_submit": "spinning.doc_events.work_order.on_submit",
	},

	"Item": {
		"validate": "spinning.doc_events.item.validate",
	},

	"Stock Reconciliation": {
		"validate": "spinning.doc_events.stock_reconciliation.validate",
		"on_submit": "spinning.doc_events.stock_reconciliation.on_submit",
		"on_cancel": "spinning.doc_events.stock_reconciliation.on_cancel",
	},
	'Sales Invoice':{
		'validate': "spinning.doc_events.sales_invoice.validate"
	}
}


# Testing
# -------

# before_tests = "spinning.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "spinning.event.get_events"
# }
import frappe
import erpnext
from erpnext.setup.doctype.naming_series.naming_series import NamingSeries


#finbyz
def get_naming_series_options(doctype):
	meta = frappe.get_meta(doctype)
	options = meta.get_field("naming_series").options.split("\n")	
	options_list = []

	fields = [d.fieldname for d in meta.fields]

	for option in options:
		flag = False
		parts = option.split('.')

		if parts[-1] == "#" * len(parts[-1]):
			del parts[-1]

		naming_str = parse_naming_series(parts)

		for part in parts:
			if part in fields:
				flag = True
				data = frappe.db.sql_list("select distinct {field} from `tab{doctype}` where {field} is not NULL".format(field=part, doctype=doctype))

				for value in data:
					series = naming_str.replace(part, value)

					if frappe.db.get_value("Series", series, 'name', order_by='name'):
						options_list.append(series)
		else:
			if not flag:
				options_list.append(option)

	return "\n".join(options_list)

def get_transactions(self, arg=None):
	doctypes = list(set(frappe.db.sql_list("""select parent
			from `tabDocField` df where fieldname='naming_series'""")
		+ frappe.db.sql_list("""select dt from `tabCustom Field`
			where fieldname='naming_series'""")))

	doctypes = list(set(get_doctypes_with_read()).intersection(set(doctypes)))
	prefixes = ""
	for d in doctypes:
		options = ""
		try:
			options = self.get_options(d)
		except frappe.DoesNotExistError:
			frappe.msgprint(_('Unable to find DocType {0}').format(d))
			#frappe.pass_does_not_exist_error()
			continue

		if options:
			options = get_naming_series_options(d)
			prefixes = prefixes + "\n" + options
	prefixes.replace("\n\n", "\n")
	prefixes = prefixes.split("\n")

	custom_prefixes = frappe.get_all('DocType', fields=["autoname"],
		filters={"name": ('not in', doctypes), "autoname":('like', '%.#%'), 'module': ('not in', ['Core'])})
	if custom_prefixes:
		prefixes = prefixes + [d.autoname.rsplit('.', 1)[0] for d in custom_prefixes]

	prefixes = "\n".join(sorted(prefixes))

	return {
		"transactions": "\n".join([''] + sorted(doctypes)),
		"prefixes": prefixes
	}

from erpnext.controllers.taxes_and_totals import get_itemised_tax, get_itemised_taxable_amount
from erpnext.regional.india.utils import get_gst_accounts
from frappe.utils import flt
def get_item_list(data, doc):
	for attr in ['cgstValue', 'sgstValue', 'igstValue', 'cessValue', 'OthValue']:
		data[attr] = 0

	gst_accounts = get_gst_accounts(doc.company, account_wise=True)
	tax_map = {
		'sgst_account': ['sgstRate', 'sgstValue'],
		'cgst_account': ['cgstRate', 'cgstValue'],
		'igst_account': ['igstRate', 'igstValue'],
		'cess_account': ['cessRate', 'cessValue']
	}
	itemNo = 0
	item_data_attrs = ['sgstRate', 'cgstRate', 'igstRate', 'cessRate', 'cessNonAdvol']
	hsn_wise_charges, hsn_taxable_amount, item_name, qty, qtyUnit = get_itemised_tax_breakup_data(doc, account_wise=True, eway=True)
	for hsn_code, taxable_amount in hsn_taxable_amount.items():
		itemNo += 1
		item_data = frappe._dict()
		if not hsn_code:
			frappe.throw(_('GST HSN Code does not exist for one or more items'))
		item_data.hsnCode = int(hsn_code)
		item_data.taxableAmount = flt(taxable_amount, 2)
		for attr in item_data_attrs:
			item_data[attr] = 0
		
		item_data.itemNo = itemNo
		item_data.productName = item_name
		item_data.productDesc = item_name
		item_data.quantity = qty
		item_data.qtyUnit = qtyUnit
		
		for account, tax_detail in hsn_wise_charges.get(hsn_code, {}).items():
			account_type = gst_accounts.get(account, '')
			for tax_acc, attrs in tax_map.items():
				if account_type == tax_acc:
					item_data[attrs[0]] = tax_detail.get('tax_rate')
					data[attrs[1]] += tax_detail.get('tax_amount')
					break
			else:
				data.OthValue += tax_detail.get('tax_amount')
		
		data.itemList.append(item_data)

		# Tax amounts rounded to 2 decimals to avoid exceeding max character limit
		for attr in ['sgstValue', 'cgstValue', 'igstValue', 'cessValue']:
			data[attr] = flt(data[attr], 2)

	return data

def get_itemised_tax_breakup_data(doc, account_wise=False, eway=False):
	itemised_tax = get_itemised_tax(doc.taxes, with_tax_account=account_wise)

	itemised_taxable_amount = get_itemised_taxable_amount(doc.items)

	if eway == True:
		qty = 0
		qtyUnit = None
		for d in doc.items:
			item_name = d.item_group
			qty += d.qty
			qtyUnit = d.uom

	if not frappe.get_meta(doc.doctype + " Item").has_field('gst_hsn_code'):
		if eway == False:
			return itemised_tax, itemised_taxable_amount
		else:
			return itemised_tax, itemised_taxable_amount, item_name, qty, qtyUnit

	item_hsn_map = frappe._dict()
	for d in doc.items:
		item_hsn_map.setdefault(d.item_code or d.item_name, d.get("gst_hsn_code"))

	hsn_tax = {}
	for item, taxes in itemised_tax.items():
		hsn_code = item_hsn_map.get(item)
		hsn_tax.setdefault(hsn_code, frappe._dict())
		for tax_desc, tax_detail in taxes.items():
			key = tax_desc
			if account_wise:
				key = tax_detail.get('tax_account')
			hsn_tax[hsn_code].setdefault(key, {"tax_rate": 0, "tax_amount": 0})
			hsn_tax[hsn_code][key]["tax_rate"] = tax_detail.get("tax_rate")
			hsn_tax[hsn_code][key]["tax_amount"] += tax_detail.get("tax_amount")

	# set taxable amount
	hsn_taxable_amount = frappe._dict()
	for item in itemised_taxable_amount:
		hsn_code = item_hsn_map.get(item)
		hsn_taxable_amount.setdefault(hsn_code, 0)
		hsn_taxable_amount[hsn_code] += itemised_taxable_amount.get(item)
	
	if eway == False:
		return hsn_tax, hsn_taxable_amount
	else:
		return hsn_tax, hsn_taxable_amount, item_name, qty, qtyUnit

NamingSeries.get_transactions = get_transactions
erpnext.regional.india.utils.get_itemised_tax_breakup_data = get_itemised_tax_breakup_data
erpnext.regional.india.utils.get_item_list = get_item_list
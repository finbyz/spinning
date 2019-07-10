# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "spinning"
app_title = "Spinning"
app_publisher = "FinByz Tech Pvt Ltd"
app_description = "Custom app for spinning app"
app_icon = "/private/files/cone-yarn.png"
app_color = "Orange"
app_email = "info@finbyz.com"
app_license = "GPL 3.0"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/spinning/css/spinning.css"
# app_include_js = "/assets/spinning/js/spinning.js"

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
		"validate": "spinning.batch_valuation.stock_entry_validate",
		"on_submit":"spinning.batch_valuation.stock_entry_on_submit",
		"on_cancel":"spinning.batch_valuation.stock_entry_on_cancel",
	},
	"Batch": {
		'before_naming': "spinning.batch_valuation.override_batch_autoname",
	},
	"Purchase Receipt": {
		"validate": "spinning.batch_valuation.pr_validate",
		"on_cancel": "spinning.batch_valuation.pr_on_cancel",
	},
	"Purchase Invoice": {
		"validate": "spinning.batch_valuation.pi_validate",
		"on_cancel": "spinning.batch_valuation.pi_on_cancel",
	},
	"Landed Cost Voucher": {
		"validate": "spinning.batch_valuation.lcv_validate",
		"on_submit": "spinning.batch_valuation.lcv_on_submit",
		"on_cancel": [
			"spinning.batch_valuation.lcv_on_cancel",
		],
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


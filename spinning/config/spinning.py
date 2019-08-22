from __future__ import unicode_literals
from frappe import _
import frappe

def get_data():

	return [
		{
			"label": _("Package"),
			"items": [
				{
					"type": "doctype",
					"name": "Package",
					"description": _("Package Master"),
					"onboard": 1,
				}
			]
		}
	]
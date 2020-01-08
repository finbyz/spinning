# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Stock Transaction"),
			"items": [
				{
					"type": "doctype",
					"name": "Material Transfer",
				},
				{
					"type": "doctype",
					"name": "Material Receipt",
				},
				{
					"type": "doctype",
					"name": "Material Issue",
				},
				{
					"type": "doctype",
					"name": "Material Unpack",
				},
				{
					"type": "doctype",
					"name": "Material Repack",
				},
				{
					"type": "doctype",
					"name": "Job Work Return",
				}
			]
		},
		{
			"label": _("General"),
			"items": [
				{
					"type": "doctype",
					"name": "Package",
				},
				{
					"type": "doctype",
					"name": "Merge",
				},
				{
					"type": "doctype",
					"name": "Grade",
				},
			]
		},
		{
			"label": _("Packing"),
			"items": [
				{
					"type": "doctype",
					"name": "Work Order Finish",
				},
				{
					"type": "doctype",
					"name": "Other Production",
				}
			]
		},
			{
			"label": _("Gate"),
			"items": [
				{
					"type": "doctype",
					"name": "Gate Entry",
				},
				{
					"type": "doctype",
					"name": "Gate Exit",
				}
			]
		},
		{
			"label": _("Report"),
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Merge Wise Balance History",
					"doctype": "Stock Ledger Entry",
					"onboard": 1,
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Sales Order Delivery Details",
					"doctype": "Sales Order",
					"onboard": 1,
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Pallet Ledger",
					"doctype": "Stock Ledger Entry",
					"onboard": 1,
				},
			]
		}
	]
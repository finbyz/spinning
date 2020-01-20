# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe import _
from spinning.controllers.batch_controller import set_batches

@frappe.whitelist()
def validate(self, method):
	if self.update_stock:
		set_batches(self, 'warehouse')

def validate_purchase_invoice(self):
	for row in self.items:
		if row.purchase_order:
			pr_name,pr_item, pr_rate = frappe.db.get_value("Purchase Order Item",row.po_detail,['name','item_code','rate'])
			if row.item_code == pr_item and row.po_detail == pr_name:
				rate = frappe.db.sql("""
								select pii.rate from `tabPurchase Order Item` as pii
								join `tabPurchase Order` as pi on (pii.parent = pi.name)
								where pii.name = %s and pi.docstatus != 2
							""", pr_name)[0][0]
				if  row.rate > flt(rate):
					frappe.throw(_("Rate can not be greater than {0} for <b>{1}</b> in row {2}").format(rate,row.item_code,row.idx))

@frappe.whitelist()
def on_submit(self, method):
	validate_purchase_invoice(self)
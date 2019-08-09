# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint


@frappe.whitelist()
def validate(self, method):
	validate_packages(self)

@frappe.whitelist()
def before_save(self, method):
	set_items_as_per_packages(self)

@frappe.whitelist()
def on_submit(self, method):
	update_packages(self, method)

@frappe.whitelist()
def on_cancel(self, method):
	update_packages(self, method)

def validate_packages(self):
	for row in self.packages:
		is_delivered = cint(frappe.db.get_value("Package", row.package, 'is_delivered'))

		if is_delivered:
			frappe.throw(_("Row {}: Package {} is already delivered. Please select another package.".format(row.idx, frappe.bold(row.package))))

def set_items_as_per_packages(self):

	package_items = list(set(map(lambda x: (x.item_code, x.merge, x.grade, x.batch_no), self.packages)))
	sales_order = list(set(map(lambda x: (x.against_sales_order, x.rate), self.items)))[0]

	item_row = self.items[0].as_dict()
	package_items = {}

	for row in self.packages:
		key = (row.item_code, row.merge, row.grade, row.batch_no)
		package_items.setdefault(key, frappe._dict({
			'net_weight': 0,
		}))
		package_items[key].update(item_row)
		package_items[key].warehouse = row.warehouse
		package_items[key].net_weight += row.net_weight

	self.set('items', [])
	
	for (item_code, merge, grade, batch_no), args in package_items.items():

		self.append('items', {
			'item_code': args.item_code,
			'item_name': args.item_name,
			'description': args.description,
			'stock_uom': args.stock_uom,
			'uom': args.uom,
			'conversion_factor': args.conversion_factor,
			'warehouse': args.warehouse,
			'rate': args.rate,
			'amount': flt(args.rate * args.net_weight),
			'merge': merge,
			'grade': grade,
			'batch_no': batch_no,
			'qty': args.net_weight,
			'against_sales_order': args.against_sales_order,
			'so_detail': args.so_detail,
		})


def update_packages(self, method):
	if method == "on_submit":
		for row in self.packages:
			doc = frappe.get_doc("Package", row.package)
			doc.delivery_document_type = self.doctype
			doc.delivery_document_no = self.name
			doc.delivery_date = self.posting_date
			doc.delivery_time = self.posting_time
			doc.outgoing_warehouse = row.warehouse
			doc.is_delivered = 1
			doc.customer = self.customer
			doc.customer_name = frappe.db.get_value("Customer", self.customer, 'customer_name')
			doc.save(ignore_permissions=True)

		else:
			frappe.db.commit()

	elif method == "on_cancel":
		for row in self.packages:
			doc = frappe.get_doc("Package", row.package)
			doc.delivery_document_type = ''
			doc.delivery_document_no = ''
			doc.delivery_date = ''
			doc.delivery_time = ''
			doc.outgoing_warehouse = ''
			doc.is_delivered = 0
			doc.customer = ''
			doc.customer_name = ''
			doc.save(ignore_permissions=True)

		else:
			frappe.db.commit()

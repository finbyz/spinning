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
		status = frappe.db.get_value("Package", row.package, 'status')

		if status == "Out of Stock":
			frappe.throw(_("Row {}: Package {} is Out of Stock. Please select another package.".format(row.idx, frappe.bold(row.package))))

def set_items_as_per_packages(self):
	to_remove = []
	items_row_dict = {}

	for row in self.items:
		has_batch_no = frappe.db.get_value("Item", row.item_code, 'has_batch_no')
		
		if has_batch_no:
			to_remove.append(row)
			items_row_dict.setdefault(row.item_code, row.as_dict())

	else:
		[self.remove(d) for d in to_remove]

	package_items = {}

	for row in self.packages:
		key = (row.item_code, row.merge, row.grade, row.batch_no)
		package_items.setdefault(key, frappe._dict({
			'net_weight': 0,
		}))
		package_items[key].update(items_row_dict.get(row.item_code))
		package_items[key].warehouse = row.warehouse
		package_items[key].net_weight += row.net_weight
	
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

	if package_items:
		for idx, row in enumerate(self.items, start = 1):
			row.idx = idx

def update_packages(self, method):
	if method == "on_submit":
		for row in self.packages:
			doc = frappe.get_doc("Package", row.package)
			doc.add_consumption(self.doctype, self.name, row.net_weight)
			doc.save(ignore_permissions=True)

	elif method == "on_cancel":
		for row in self.packages:
			doc = frappe.get_doc("Package", row.package)
			doc.remove_consumption(self.doctype, self.name)
			doc.save(ignore_permissions=True)

# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint
from erpnext.stock.doctype.batch.batch import set_batch_nos
from erpnext.stock.doctype.delivery_note.delivery_note import DeliveryNote
from spinning.controllers.batch_controller import set_batches


def before_validate(self, method):
	if self.is_return == 0:
		validate_packages(self)

def before_save(self, method):
	calculate_totals(self)
	set_pallet_item(self)

def on_submit(self, method):
	update_packages(self, method)
	create_pallet_stock_entry(self)
	for item in self.items:
		if item.against_pick_list:
			pick_list_item = frappe.get_doc("Pick List Item", item.against_pick_list)
			delivered_qty = item.qty + pick_list_item.delivered_qty
			if delivered_qty > pick_list_item.qty:
				frappe.throw(f"Row {item.idx}: You can not deliver more tha picked qty")
			pick_list_item.db_set("delivered_qty", delivered_qty)

def on_cancel(self, method):
	update_packages(self, method)
	cancel_pallet_stock_entry(self)
	for item in self.items:
		if item.against_pick_list:
			pick_list_item = frappe.get_doc("Pick List Item", item.against_pick_list)
			delivered_qty = pick_list_item.delivered_qty - item.qty
			if delivered_qty < 0:
				delivered_qty = 0
				# frappe.throw("You can not deliver more tha picked qty")
				pass
			pick_list_item.db_set("delivered_qty", delivered_qty)

def validate_packages(self):
	for row in self.packages:
		status = frappe.db.get_value("Package", row.package, 'status')

		if status == "Out of Stock":
			frappe.throw(_("Row {}: Package {} is Out of Stock. Please select another package.".format(row.idx, frappe.bold(row.package))))

def set_pallet_item(self):
	finish_list = []
	result = {}
	if self.package_type == "Pallet":
		for row in self.packages:
			if row.sheet_item or row.package_item:
				finish_list.append({row.sheet_item:row.no_of_sheets,row.package_item:1})

		for d in finish_list:
			for k in d.keys():
				result[k] = result.get(k, 0) + d[k]

		self.pallet_item = []
		for k,v in result.items():
			self.append('pallet_item',{
				'pallet_item': k,
				'qty': v
			})

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
			'gross_weight': 0,
			'packages': 0,
			'no_of_spools': 0,
		}))

		package_items[key].update(items_row_dict.get(row.item_code))
		package_items[key].warehouse = row.warehouse
		package_items[key].net_weight += row.consumed_qty
		package_items[key].gross_weight += row.gross_weight
		package_items[key].no_of_spools += row.spools
		package_items[key].packages += 1

	for (item_code, merge, grade, batch_no), args in package_items.items():
		amount = flt(args.rate * args.net_weight)

		values = args.copy()
		values.pop('idx')
		values.pop('name')
		values.amount = amount
		values.merge = merge
		values.grade = grade
		values.batch_no = batch_no
		values.qty = args.net_weight
		values.gross_wt = args.gross_weight
		values.spools = args.no_of_spools
		values.no_of_packages = args.packages

		self.append('items', values)

	if package_items:
		for idx, row in enumerate(self.items, start = 1):
			row.idx = idx

def calculate_totals(self):
	self.total_gr_wt = sum([row.gross_wt for row in self.items])

def update_packages(self, method):
	if method == "on_submit":
		if self.is_return:
			for row in self.packages:
				doc = frappe.get_doc("Package", row.package)
				doc.add_consumption(self.doctype, self.name, -row.consumed_qty, self.posting_date, self.posting_time)
				doc.save(ignore_permissions=True)
		else:
			for row in self.packages:
				doc = frappe.get_doc("Package", row.package)
				doc.add_consumption(self.doctype, self.name, row.consumed_qty, self.posting_date, self.posting_time)
				doc.save(ignore_permissions=True)

	elif method == "on_cancel":
		for row in self.packages:
			doc = frappe.get_doc("Package", row.package)
			doc.remove_consumption(self.doctype, self.name)
			doc.save(ignore_permissions=True)

def create_pallet_stock_entry(self):

	if self.pallet_item and self.is_returnable:
		abbr = frappe.db.get_value('Company',self.company,'abbr')
		pallet_se = frappe.new_doc("Stock Entry")
		pallet_se.stock_entry_type = "Material Transfer"
		pallet_se.purpose = "Material Transfer"
		pallet_se.posting_date = self.posting_date
		pallet_se.posting_time = self.posting_time
		pallet_se.set_posting_time = self.set_posting_time
		pallet_se.company = self.company
		pallet_se.reference_doctype = self.doctype
		pallet_se.reference_docname = self.name
		pallet_se.party_type = "Customer"
		pallet_se.party = self.customer
		pallet_se.returnable_by = self.returnable_by

		if self.is_return:
			for row in self.pallet_item:
				rate = frappe.db.get_value("Item",row.pallet_item,'valuation_rate')
				pallet_se.append("items",{
					'item_code': row.pallet_item,
					'qty': row.qty,
					'basic_rate': rate or 0,
					's_warehouse': row.t_warehouse,
					't_warehouse': row.s_warehouse
					#'allow_zero_valuation_rate': 1
				})
			try:
				pallet_se.save(ignore_permissions=True)
				pallet_se.submit()
			except Exception as e:
				frappe.throw(str(e))

		else:
			for row in self.pallet_item:
				rate = frappe.db.get_value("Item",row.pallet_item,'valuation_rate')
				pallet_se.append("items",{
					'item_code': row.pallet_item,
					'qty': row.qty,
					'basic_rate': rate or 0,
					's_warehouse': row.s_warehouse,
					't_warehouse': row.t_warehouse
					#'allow_zero_valuation_rate': 1
				})
			try:
				pallet_se.save(ignore_permissions=True)
				pallet_se.submit()
			except Exception as e:
				frappe.throw(str(e))

def cancel_pallet_stock_entry(self):
	if self.pallet_item and self.is_returnable:
		se = frappe.get_doc("Stock Entry",{'reference_doctype': self.doctype,'reference_docname':self.name})
		se.flags.ignore_permissions = True
		try:
			se.cancel()
		except Exception as e:
			raise e
		se.db_set('reference_doctype','')
		se.db_set('reference_docname','')	
		


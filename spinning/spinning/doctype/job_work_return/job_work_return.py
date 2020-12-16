# -*- coding: utf-8 -*-
# Copyright (c) 2019, FinByz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils import nowdate, flt, cint
from erpnext.stock.utils import get_incoming_rate
from frappe.model.delete_doc import check_if_doc_is_linked
from erpnext.stock.stock_ledger import get_previous_sle
from spinning.controllers.batch_controller import set_batches
from erpnext.stock.get_item_details import get_bin_details, get_default_cost_center, get_conversion_factor, get_reserved_qty_for_so
from erpnext.setup.doctype.item_group.item_group import get_item_group_defaults
from erpnext.setup.doctype.brand.brand import get_brand_defaults
from six import string_types
from datetime import datetime
from spinning.controllers.batch_controller import get_batch_no
from frappe.utils import flt, cstr, cint


class JobWorkReturn(Document):
	def validate(self):
		self.validate_weights()
	
	def on_submit(self):
		for row in self.items:
			has_batch_no = frappe.db.get_value('Item', self.item_code, 'has_batch_no')
			if has_batch_no and not batch_no:
				frappe.throw(_("Row:{} Merge and grade is manadatory for item {}".format(row.idx,row.item_code))

				
		self.create_packages()
		self.create_stock_entry()

	def before_save(self):
		self.set_batch()
		for row in self.package_details:
			row.tare_weight = row.gross_weight - row.net_weight
		
	def on_cancel(self):
		self.clear_package_weight()
		self.cancel_stock_entry()

	def validate_weights(self):
		#for row in self.package_details:
			# has_batch_no = frappe.db.get_value('Item', row.item_code, 'has_batch_no')
			# frappe.msgprint(__("wght called."))
		total_net_weight = sum(map(lambda x: x.net_weight, self.package_details))

		if flt(self.qty != flt(round(total_net_weight,3))):
			frappe.throw(_("Total Qty {} does not match with Package Weight {}".format(self.qty,round(total_net_weight,3))))
			
	
	def create_stock_entry(self):
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Repack"
		se.purpose = "Repack"
		se.set_posting_time = 1
		se.reference_doctype = self.doctype
		se.reference_docname = self.name
		se.posting_date = self.posting_date
		se.posting_time = self.posting_time
		se.company = self.company
		
		for row in self.items:
			se.append("items",{
				'item_code': row.item_code,
				's_warehouse': self.s_warehouse,
				'qty': row.qty,
				'batch_no':row.batch_no,
				'merge': row.merge,
				'grade': row.grade,
			})
		se.append("items",{
			'item_code': self.item_code,
			't_warehouse': self.t_warehouse,
			'merge': self.merge,
			'grade': self.grade,
			'batch_no': self.batch_no,
			'qty': self.total_net_weight,
		})
		for row in self.additional_cost:
			se.append("additional_costs",{
				'description': row.description,
				'amount': row.amount
			})
		#se.get_stock_and_rate()
		try:
			se.save(ignore_permissions=True)
			se.submit()
			self.add_package_consumption()

		except Exception as e:
			frappe.throw(str(e))

	def cancel_stock_entry(self):
		se = frappe.get_doc("Stock Entry",{'reference_doctype': self.doctype,'reference_docname':self.name})
		se.flags.ignore_permissions = True
		try:
			se.cancel()
		except Exception as e:
			raise e
		self.remove_package_consumption()
		se.db_set('reference_doctype','')
		se.db_set('reference_docname','')

	def clear_package_weight(self):
		package_list = frappe.get_list("Package",filters={'purchase_document_type':self.doctype,'purchase_document_no':self.name})		
		for row in package_list:		
			doc = frappe.get_doc("Package", row.name)	
			if doc.status != "In Stock":
				frappe.throw(_("#Row {}: This Package is Partial Stock or Out of Stock.".format(row.idx)))

			doc.net_weight = 0
			doc.gross_weight = 0
			doc.spool_weight = 0
			doc.tare_weight = 0
			doc.purchase_document_no = ''
			doc.save(ignore_permissions=True)

		else:
			frappe.db.commit()

	def add_package_consumption(self):
		total_remaining_qty = 0
		for row in self.items:
			if self.s_warehouse:
				remaining_qty = row.qty
				package_list = frappe.db.sql(""" select name, remaining_qty from `tabPackage` 
					where status <> "Out of Stock" and merge = %s and item_code = %s and warehouse = %s""", (row.merge, row.item_code,self.s_warehouse), as_dict = True)
	
				total_remaining_qty = sum(flt(d.remaining_qty) for d in package_list)

				if total_remaining_qty < flt(row.qty):
					frappe.throw(_("Sufficient quantity for item {} is not available in {} warehouse for merge {}.".format(frappe.bold(row.item_code), frappe.bold(self.s_warehouse), frappe.bold(row.merge))))
				for pkg in package_list:
					doc = frappe.get_doc("Package", pkg.name)
					qty = doc.remaining_qty if remaining_qty > doc.remaining_qty else remaining_qty
					doc.add_consumption(self.doctype, self.name, qty, self.posting_date, self.posting_time)
					doc.save(ignore_permissions=True)
					remaining_qty -= qty
					
					if remaining_qty <= 0:
						break

	def remove_package_consumption(self):
		package_list = frappe.get_list("Package Consumption", filters = {
				'reference_doctype': self.doctype,
				'reference_docname': self.name
			}, fields = 'parent')

		for pkg in package_list:
			doc = frappe.get_doc("Package", pkg.parent)
			doc.remove_consumption(self.doctype, self.name)
			doc.save(ignore_permissions=True)

	def set_batch(self):
		has_batch_no = frappe.db.get_value('Item', self.item_code, 'has_batch_no')

		if has_batch_no:
			if not self.get('merge'):
				frappe.throw(_("Please set Merge"))

			if not self.get('grade'):
				frappe.throw(_("Please set Grade"))

			args = {
				'item_code': self.item_code,
				'merge': self.merge,
				'grade': self.grade,
			}

			batch_no = get_batch_no(args)

			if not batch_no:
				batch = frappe.new_doc("Batch")
				batch.item = self.item_code
				batch.grade = cstr(self.grade)
				batch.merge = cstr(self.merge)
				batch.insert(ignore_permissions=True)
				batch_no = batch.name

			self.db_set('batch_no', batch_no)

	def create_packages(self):
		def validate_package_type():
			if not self.get('default_package_type'):
				return False
			return True

		if self.get('package_details'):
			if not validate_package_type():
				frappe.throw(_("Please select Package Type!"))

		for pkg in self.package_details:
			doc = frappe.new_doc("Package")
			doc.package_no = pkg.package
			doc.package_type = pkg.package_type
			doc.package_item = pkg.package_item
			doc.company = self.company
			doc.item_code = self.item_code


			if pkg.package_type == "Pallet":
				doc.is_returnable = pkg.is_returnable
				doc.returnable_by = pkg.returnable_by

			doc.gross_weight = pkg.gross_weight
			doc.net_weight = pkg.net_weight
			doc.tare_weight = pkg.tare_weight
			doc.spools = pkg.spools
			
			# doc.batch_no = row.batch_no
			# doc.item_code = row.item_code
			# doc.item_name = row.item_name
			# doc.merge = row.merge
			# doc.grade = row.grade

			doc.purchase_document_type = self.doctype
			doc.purchase_document_no = self.name
			doc.purchase_date = self.posting_date
			doc.purchase_time = self.posting_time
			doc.batch_no = self.batch_no
			doc.merge = self.merge
			doc.grade = self.grade
			# doc.incoming_rate = row.basic_rate
			doc.warehouse = self.t_warehouse
			
			doc.save(ignore_permissions=True)

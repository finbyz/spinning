# -*- coding: utf-8 -*-
# Copyright (c) 2019, FinByz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cstr
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

from spinning.doc_events.work_order import override_work_order_functions
from spinning.controllers.batch_controller import get_batch_no, get_fifo_batches

import json
from six import string_types


class WorkOrderFinish(Document):
	def before_save(self):
		if not self.is_new():
			self.set_batch()

		self.set_missing_packages()

	def set_batch(self):
		if self.get('batch_no'):
			return

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
				batch.insert()
				batch_no = batch.name

			self.db_set('batch_no', batch_no)

	def set_missing_packages(self):
		for row in self.package_details:
			# frappe.errprint(str(row.get('__islocal')))
			if not row.get('package'):
				self.print_row_package(row, False)

	def print_row_package(self, child_row, commit=True):
		# frappe.errprint(str(type(child_row)))
		self.set_batch()

		def get_package_doc(source_name, target_doc=None):
			def set_missing_values(source, target):
				if source.package_type == "Pallet":
					target.ownership_type = "Company"
					target.ownership = source.company

			return get_mapped_doc("Work Order Finish", source_name, {
				"Work Order Finish": {
					"doctype": "Package",
					"field_map": {
						"series": "package_series",
						"target_warehouse": "warehouse",
						"posting_date" : "purchase_date",
						"posting_time" : "purchase_time",
					}
				}
			}, target_doc, set_missing_values)

		if isinstance(child_row, dict):
			child_row = frappe._dict(child_row)
			
			if child_row.get('__islocal'):
				child_row = self.get_child_doc(child_row)
				child_row.insert()

			else:
				child_row = frappe.get_doc(child_row.doctype, child_row.name)


		if frappe.db.exists("Package", child_row.package):
			package = frappe.get_doc("Package", child_row.package)
			
		else:
			package = get_package_doc(self.name)

		package.gross_weight = child_row.gross_weight
		package.net_weight = child_row.net_weight
		package.tare_weight = child_row.tare_weight
		package.spools = child_row.no_of_spool
		package.package_weight = child_row.package_weight
		package.save(ignore_permissions=True)

		# if child_row.get('__islocal'):
		# 	row = self.get_child_doc(child_row)
		# 	row.package = package.name
		# 	row.insert()

		# else:
		# 	row = frappe.get_doc(child_row.doctype, child_row.name)
		if not child_row.package:
			child_row.package = package.name

		if commit:
			child_row.save()

	def get_child_doc(self, child_row):
		def parse_args(child_row):
			child_row.pop('__islocal')
			child_row.pop('__unsaved')
			child_row.pop('__unedited')
			child_row.pop('name')

			return child_row

		child_row = parse_args(child_row)

		doc = frappe.get_doc(child_row)
		return doc

	def on_submit(self):
		self.create_stock_entry()
		self.update_packages()

	def on_cancel(self):
		self.cancel_stock_entry()

	def create_stock_entry(self):
		wo = frappe.get_doc("Work Order", self.work_order)
		
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Manufacture"
		se.purpose = "Manufacture"
		se.work_order = self.work_order
		se.bom_no = self.from_bom
		se.set_posting_time = 1
		se.posting_date = self.posting_date
		se.posting_time = self.posting_time
		se.from_bom = 1
		se.company = self.company
		se.fg_completed_qty = self.total_net_weight
		se.from_warehouse = wo.wip_warehouse
		
		se.get_items()

		if self.paper_tube:
			se.append("items",{
				'item_code': self.paper_tube,
				's_warehouse': wo.wip_warehouse,
				'qty': self.total_spool,
			})

		se.append("items",{
			'item_code': self.package_item,
			's_warehouse': self.source_warehouse,
			'qty': len(self.package_details),
		})

		for d in se.items:
			if d.t_warehouse and d.item_code == self.item_code:
				d.merge = self.merge
				d.grade = self.grade

			if d.s_warehouse:
				merge = frappe.db.sql("select merge from `tabWork Order Item` where parent = %s and item_code = %s", (self.work_order, d.item_code))
				if merge:
					d.merge = merge[0][0]

		override_work_order_functions()
		items = []

		for d in se.items:
			if not d.s_warehouse:
				continue

			elif not d.merge:
				continue

			has_batch_no = frappe.db.get_value('Item', d.item_code, 'has_batch_no')

			if not has_batch_no:
				continue

			batches = get_fifo_batches(d.item_code, d.s_warehouse, d.merge)

			if not batches:
				frappe.throw(_("Sufficient quantity for item {} is not available in {} warehouse.".format(frappe.bold(d.item_code), frappe.bold(d.s_warehouse))))

			remaining_qty = d.qty

			for i, batch in enumerate(batches):
				if i == 0:
					if batch.qty >= remaining_qty:
						d.batch_no = batch.batch_id
						break

					else:
						if len(batches) == 1:
							frappe.throw(_("Sufficient quantity for item {} is not available in {} warehouse.".format(frappe.bold(d.item_code), frappe.bold(d.s_warehouse))))

						remaining_qty -= flt(batch.qty)
						d.qty = batch.qty
						d.batch_no = batch.batch_id

						items.append(frappe._dict({
							'item_code': d.item_code,
							's_warehouse': wo.wip_warehouse,
							'qty': remaining_qty,
						}))

				else:
					flag = 0
					for x in items[:]:
						if x.get('batch_no'):
							continue

						if batch.qty >= remaining_qty:
							x.batch_no = batch.batch_id
							flag = 1
							break
						
						else:
							remaining_qty -= flt(batch.qty)
							
							x.qty = batch.qty
							x.batch_no = batch.batch_id
							
							items.append(frappe._dict({
								'item_code': d.item_code,
								's_warehouse': wo.wip_warehouse,
								'qty': remaining_qty,
							}))

					if flag:
						break

			else:
				if remaining_qty:
					frappe.throw(_("Sufficient quantity for item {} is not available in {} warehouse.".format(frappe.bold(d.item_code), frappe.bold(d.s_warehouse))))

		se.extend('items', items)

		for row in se.items:
			if row.s_warehouse:
				frappe.msgprint("Row {} : Item Code - {}, Batch No - {}, Merge - {}".format(row.idx, row.item_code, row.batch_no, row.merge))

		se.save(ignore_permissions=True)
		se.submit()
		self.db_set('stock_entry', se.name)

	def update_packages(self):
		if self._action == "submit":
			for row in self.package_details:
				doc = frappe.get_doc("Package", row.package)
				doc.add_consumption(self.doctype, self.name, row.net_weight)
				doc.save(ignore_permissions=True)

		elif self._action == "cancel":
			for row in self.package_details:
				doc = frappe.get_doc("Package", row.package)
				doc.remove_consumption(self.doctype, self.name)
				doc.save(ignore_permissions=True)
				
	def cancel_stock_entry(self):
		if self.stock_entry:
			se = frappe.get_doc("Stock Entry", self.stock_entry)
			override_work_order_functions()
			se.cancel()
			self.db_set('stock_entry','')
			frappe.db.commit()

# -*- coding: utf-8 -*-
# Copyright (c) 2019, FinByz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc

class MaterialUnpack(Document):
	def on_submit(self):
		if not self.batch_no:
			frappe.throw(_("Sufficient quantity for item {} is not available in {} warehouse for merge {}.".format(frappe.bold(self.item_code), frappe.bold(self.warehouse), frappe.bold(self.merge))))
		self.create_stock_entry()
				
	def on_cancel(self):
		self.cancel_stock_entry()
		
	def create_stock_entry(self):
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Material Transfer"
		se.purpose = "Material Transfer"
		se.posting_date = self.posting_date
		se.posting_time = self.posting_time
		se.company = self.company
		abbr = frappe.db.get_value('Company',self.company,'abbr')
	
		se.append("items",{
			'item_code': self.item_code,
			'qty': self.total_net_weight,
			's_warehouse': self.s_warehouse,
			't_warehouse': self.t_warehouse,
			'merge': self.merge,
			'grade': self.grade,
			'batch_no': self.batch_no
		})
		try:
			se.save(ignore_permissions=True)
			se.submit()
			self.db_set('stock_entry_ref', se.name)
			self.update_packages()
			frappe.db.commit()
		except Exception as e:
			frappe.throw(str(e))
			
	def cancel_stock_entry(self):
		if self.stock_entry_ref:
			se = frappe.get_doc("Stock Entry", self.stock_entry_ref)
			se.cancel()
			self.db_set('stock_entry_ref', None)

		self.update_packages()
		
	def update_packages(self):
		if self._action == "submit":
			for row in self.packages:
				doc = frappe.get_doc("Package", row.package)
				doc.warehouse = self.t_warehouse
				doc.save(ignore_permissions=True)

		elif self._action == "cancel":
			for row in self.packages:
				doc = frappe.get_doc("Package", row.package)
				doc.warehouse = self.s_warehouse
				doc.save(ignore_permissions=True)
				
@frappe.whitelist()
def make_repack(source_name, target_doc=None):
	# def postprocess(source, target):
		# target.append('items', {
			# 'item_code': source.product_name,
			# 'item_name': source.product_name,
			# 'base_cost' : source.per_unit_price
			# })

	doclist = get_mapped_doc("Material Unpack" , source_name,{
		"Material Unpack":{
			"doctype" : "Material Repack",
			"field_map":{
				"batch_no" : "batch_no",
				'name': 'material_unpack'
			},
			"field_no_map":[
				"naming_series",
				"total_net_weight",
				"total_gross_weight",
				"posting_date",
				"posting_time"
			]
		}
	},target_doc)

	return doclist
# -*- coding: utf-8 -*-
# Copyright (c) 2019, FinByz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document
from frappe.model.naming import make_autoname

from spinning.controllers.batch_controller import get_batch_no

class Package(Document):
	def autoname(self):
		if self.package_series:
			series = self.package_series + '.######'
			
			name = None
			while not name:
				name = make_autoname(series, "Package", self)
				if frappe.db.exists('Package', name):
					name = None
			
			self.package_no = name
			self.name = name

	def validate(self):
		self.set_batch_no()
		self.calculate_consumption()

	def set_batch_no(self):
		if not self.batch_no:
			args = frappe._dict()
			args.item_code = self.item_code
			args.grade = self.grade
			args.merge = self.merge

			batch_no = get_batch_no(args)

			if not batch_no:
				frappe.throw(_("No related batch found for Grade {} and Merge {}".format(frappe.bold(self.grade), frappe.bold(self.merge))))

			self.batch_no = batch_no
			
	def before_save(self):
		self.update_status()

	def calculate_consumption(self):
		self.total_consumed_qty = sum([flt(row.consumed_qty) for row in self.consumptions])
		self.remaining_qty = flt(self.net_weight - self.total_consumed_qty)
		
	def update_status(self):
		status = None

		if self.remaining_qty == self.net_weight:
			status = "In Stock"

		elif self.remaining_qty == 0:
			status = "Out of Stock"

		else:
			status = "Partial Stock"

		if self.status != status:
			self.db_set("status", status)

	def add_consumption(self, doctype, docname, qty):
		for row in self.consumptions:
			if row.reference_doctype == doctype and row.reference_docname == docname:
				frappe.throw(_("Package already consumed for %s : %s" % (doctype, docname)))

		self.append('consumptions', {
			'reference_doctype': doctype,
			'reference_docname': docname,
			'consumed_qty': flt(qty)
		})

	def remove_consumption(self, doctype, docname):
		to_remove = []

		for row in self.consumptions:
			if row.reference_doctype == doctype and row.reference_docname == docname:
				to_remove.append(row)

		else:
			[self.remove(d) for d in to_remove]

		self.calculate_consumption()

@frappe.whitelist()
def get_packages(filters):
	fields = ('name', 'spools', 'item_code', 'item_name', 'warehouse', 'batch_no', 'merge', 'grade', 'gross_weight', 'net_weight', 'tare_weight')

	data = frappe.get_list("Package", filters = filters, fields = fields)

	for row in data:
		row.package = row.pop('name')

	return data

# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cstr

def set_batches(self, warehouse_field):
	if self._action == 'submit':
		for row in self.items:
			if not row.get(warehouse_field):
				continue

			has_batch_no = frappe.db.get_value('Item', row.item_code, 'has_batch_no')

			if has_batch_no:
				if not row.get('merge'):
					frappe.throw(_("Please set Merge in row {}".format(row.idx)))

				if not row.get('grade'):
					frappe.throw(_("Please set Grade in row {}".format(row.idx)))

				batch_nos = frappe.db.sql_list(""" select name from `tabBatch` 
					where grade = %s and merge = %s and item = %s """, (row.grade, row.merge, row.item_code))

				if batch_nos:
					row.batch_no = batch_nos[0]

				else:
					batch = frappe.new_doc("Batch")
					batch.item = row.item_code
					batch.supplier = getattr(self, 'supplier', None)
					batch.packaging_material = cstr(row.packaging_material)
					batch.packing_size = cstr(row.packing_size)
					batch.grade = cstr(row.grade)
					batch.merge = cstr(row.merge)
					batch.reference_doctype = self.doctype
					batch.reference_name = self.name
					batch.insert()
					row.batch_no = batch.name

			elif row.grade or row.merge:
				frappe.throw(_("Please clear Grade and Merge for Item {} as it is not batch wise item in row {}".format(row.item_code, row.idx)))
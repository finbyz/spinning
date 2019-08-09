# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
from frappe import _

from spinning.controllers.batch_controller import set_batches

@frappe.whitelist()
def stock_entry_validate(self, method):
	if self._action == 'submit':
		set_batches(self, 't_warehouse')
	else:
		validate_batch_details(self)

	if self.purpose in ["Repack", "Manufacture"]:
		self.run_method("get_stock_and_rate")

def validate_batch_details(self):
	wo_merge = None

	if self.get('work_order'):
		wo_merge = frappe.db.get_value("Work Order", self.work_order, 'merge')
	
	for row in self.items:
		has_batch_no = frappe.db.get_value('Item', row.item_code, 'has_batch_no')

		if has_batch_no:
			if row.s_warehouse and row.batch_no:
				row.merge, row.grade = frappe.db.get_value("Batch", row.batch_no, ['merge', 'grade'])

			elif row.t_warehouse and wo_merge and row.merge != wo_merge:
				frappe.throw(_("#Row {}: Merge should be same as Work Order Merge!".format(row.idx)))

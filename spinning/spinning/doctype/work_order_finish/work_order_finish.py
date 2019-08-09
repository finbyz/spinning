# -*- coding: utf-8 -*-
# Copyright (c) 2019, FinByz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class WorkOrderFinish(Document):
	def create_package(self,child_row,ignore_permissions=True):
		for row in self.work_order_finish_detail:
			if frappe.db.exists("Package",row.package):
				package = frappe.get_doc("Package",row.package)
				package.gross_weight = row.gross_weight
				package.net_weight = row.net_weight
				package.tare_weight = row.tare_weight
				package.spools = row.no_of_spool
				package.package_weight = row.package_weight
				
				package.save(ignore_permissions=True)
				
			else:
				package = frappe.new_doc("Package")
				package.package_series = self.series
				package.package_type = self.package_type
				package.is_returnable = self.is_returnable
				package.spools = row.no_of_spool
				package.spool_color = self.spool_color
				package.company = self.company
				package.gross_weight = row.gross_weight
				package.spool_weight = self.spool_weight
				package.package_weight = row.package_weight
				package.net_weight = row.net_weight
				package.tare_weight = row.tare_weight
				package.item_code = self.item_code
				package.item_name = self.item_name
				package.merge = self.merge
				package.grade = self.grade
				package.purchase_document_type = "Work Order"
				package.purchase_document_no = self.work_order
				package.purchase_date = self.posting_date
				package.purchase_time = self.posting_time
				
				package.save(ignore_permissions=True)
				row.db_set("package",package.name)
			return package
			
	
	def on_submit(self):
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.purpose = "Manufacture"
		stock_entry.work_order = self.work_order
		stock_entry.company = self.company
		stock_entry.fg_completed_qty = self.total_net_weight
		
		stock_entry.save()
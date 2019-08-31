# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint
from frappe.model.delete_doc import check_if_doc_is_linked

from spinning.controllers.batch_controller import set_batches

@frappe.whitelist()
def validate(self, method):
	set_batches(self, 'warehouse')

	if self._action == 'submit':
		validate_weights(self)

@frappe.whitelist()
def on_submit(self, method):
	create_packages(self)

@frappe.whitelist()
def on_cancel(self, method):
	delete_packages(self)

def validate_weights(self):
	for row in self.items:
		has_batch_no = frappe.db.get_value('Item', row.item_code, 'has_batch_no')

		if has_batch_no:
			total_net_weight = sum(map(lambda x: x.net_weight if x.row_ref == str(row.idx) else 0, self.packages))

			if flt(row.qty, row.precision('qty')) != flt(total_net_weight, row.precision('qty')):
				frappe.throw(_("Total Qty does not match with Total Net Weight for Item {} in Row {}".format(row.item_code, row.idx)))

def create_packages(self):
	def validate_package_type():
		if not self.get('package_type'):
			return False
		return True

	def get_row_doc(row_no):
		if len(self.items) < row_no:
			frappe.throw(_("Row Ref in Package List is greater that total rows of Items."))
		return self.items[row_no - 1]

	if self.get('packages'):
		if not validate_package_type():
			frappe.throw(_("Please select Package Type!"))

	for pkg in self.packages:
		row = get_row_doc(cint(pkg.row_ref))

		has_batch_no = frappe.db.get_value('Item', row.item_code, 'has_batch_no')
		
		if not has_batch_no:
			frappe.throw(_("Item {} is not batch wise in Row {}".format(frappe.bold(row.item_code), row.idx)))

		doc = frappe.new_doc("Package")
		doc.package_no = pkg.package
		doc.package_type = self.package_type
		doc.package_item = self.package_item
		doc.spools = cint(pkg.spools)
		doc.company = self.company
		doc.warehouse = row.warehouse

		if self.package_type == "Pallet":
			doc.is_returnable = self.is_returnable
			doc.returnable_by = self.returnable_by

		doc.gross_weight = pkg.gross_weight
		doc.net_weight = pkg.net_weight

		doc.batch_no = row.batch_no
		doc.item_code = row.item_code
		doc.item_name = row.item_name
		doc.merge = row.merge
		doc.grade = row.grade

		doc.purchase_document_type = self.doctype
		doc.purchase_document_no = self.name
		doc.purchase_date = self.posting_date
		doc.purchase_time = self.posting_time
		doc.incoming_rate = row.valuation_rate
		doc.ownership_type = "Supplier"
		doc.ownership = self.supplier
		doc.supplier = self.supplier
		doc.supplier_name = frappe.db.get_value("Supplier", self.supplier, 'supplier_name')

		doc.save(ignore_permissions=True)

def delete_packages(self):
	for row in self.packages:
		doc = frappe.get_doc("Package", row.package)
		if cint(doc.get('is_delivered')):
			frappe.throw(_("#Row {}: This Package is already delivered with document reference {}.".format(row.idx, frappe.bold(doc.delivery_document_no))))

		check_if_doc_is_linked(doc)
		frappe.delete_doc("Package", doc.name,ignore_permissions=True)

	else:
		frappe.db.commit()

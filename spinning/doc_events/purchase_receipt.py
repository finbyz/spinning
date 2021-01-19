# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint
from frappe.model.delete_doc import check_if_doc_is_linked
from spinning.controllers.merge_validation import validate_merge
from spinning.controllers.batch_controller import set_batches

@frappe.whitelist()
def validate(self, method):
	set_batches(self, 'warehouse')
	if self._action == 'submit':
		validate_purchase_receipt(self)
		validate_package_qty(self)
		if self.is_return:
			validate_packages(self)
		else:
			validate_gate_pass(self)
			
	calculate_gst_taxable_value(self)


@frappe.whitelist()
def before_save(self, method):
	pass
	#update_pallet_item(self)

@frappe.whitelist()
def on_submit(self, method):
	if self.is_return:
		update_packages(self, method)
		cancel_pallet_stock_entry(self)
		remove_package_consumption(self)
	else:
		create_packages(self)
		create_pallet_stock_entry(self)
		add_package_consumption(self)

	
@frappe.whitelist()
def on_cancel(self, method):
	validate_package(self)
	if self.is_return:
		update_packages(self, method)
		create_pallet_stock_entry(self)
		add_package_consumption(self)		
	else:	
		clear_package_weight(self)	
		cancel_pallet_stock_entry(self)
		remove_package_consumption(self)

def calculate_gst_taxable_value(self):
    account_list = []
    gst_setting = frappe.get_single("GST Settings")
    for row in gst_setting.gst_accounts:
        if row.company == self.company:
            account_list.append(row.cgst_account)
            account_list.append(row.sgst_account)
            account_list.append(row.igst_account)
    for d in self.taxes:
        if d.account_head in account_list:
            self.gst_taxable_value = flt(d.base_total) - flt(d.base_tax_amount)
            break

def validate_package(self):
	package_list = frappe.get_list("Package",filters={'purchase_document_type':self.doctype,'purchase_document_no':self.name})		
	for row in package_list:		
		doc = frappe.get_doc("Package", row.name)
		if doc.warehouse != self.set_warehouse:
			frappe.throw(_("Package {} does not belong to warehouse {}.".format(doc.name,self.set_warehouse)))
			
		
def validate_purchase_receipt(self):
	for row in self.items:
		if row.warehouse and row.warehouse != self.set_warehouse:
			frappe.throw(_("Row {} : Warehouse should same as {} for item {}").format(row.idx,self.set_warehouse,row.item_code))
		if row.purchase_order:
			pr_name, pr_item, pr_rate = frappe.db.get_value("Purchase Order Item",row.purchase_order_item,['name','item_code','rate'])

			if row.item_code == pr_item and row.purchase_order_item == pr_name:
				rate = frappe.db.sql("""
								select pii.rate from `tabPurchase Order Item` as pii
								join `tabPurchase Order` as pi on (pii.parent = pi.name)
								where pii.name = %s and pi.docstatus != 2
							""", pr_name)[0][0]
				if  row.rate > flt(rate):
					frappe.throw(_("Rate can not be greater than {0} for <b>{1}</b> in row {2}").format(rate,row.item_code,row.idx))


def validate_gate_pass(self):
	if self.gate_entry_no == 0:
		frappe.throw(_("Please Enter Gate Pass No"))
		

def validate_packages(self):
	for row in self.packages:
		status = frappe.db.get_value("Package", row.package, 'status')

		if status == "Out of Stock":
			frappe.throw(_("Row {}: Package {} is Out of Stock. You can not return package which is not in stock".format(row.idx, frappe.bold(row.package))))

def validate_package_qty(self):
	for row in self.items:
		has_batch_no = frappe.db.get_value('Item', row.item_code, 'has_batch_no')

		if cint(has_batch_no):
			if self.is_return:
				total_net_weight = sum([-d.net_weight for d in self.packages if row.idx == cint(d.row_ref)])
			else:
				total_net_weight = sum([d.net_weight for d in self.packages if row.idx == cint(d.row_ref)])

			if flt(row.qty, 4) != flt(total_net_weight, 4):
				frappe.throw(_("#Row {}: Total Net Weight for Item - {} in packages is {}, which doesn't match the Qty {} in Items.".format(row.idx, frappe.bold(row.item_code), total_net_weight, row.qty)), title = "Total Package Error!")


def create_pallet_stock_entry(self):
	if self.pallet_item and self.is_returnable:
		abbr = frappe.db.get_value('Company',self.company,'abbr')
		pallet_se = frappe.new_doc("Stock Entry")
		pallet_se.stock_entry_type = "Material Receipt"
		pallet_se.purpose = "Material Receipt"
		pallet_se.posting_date = self.posting_date
		pallet_se.posting_time = self.posting_time
		pallet_se.set_posting_time = self.set_posting_time
		pallet_se.company = self.company
		pallet_se.reference_doctype = self.doctype
		pallet_se.reference_docname = self.name
		pallet_se.party_type = "Supplier"
		pallet_se.party = self.supplier
		pallet_se.returnable_by = self.returnable_by
		
		for row in self.pallet_item:
			rate = frappe.db.get_value("Item",row.pallet_item,'valuation_rate')
			pallet_se.append("items",{
				'item_code': row.pallet_item,
				'qty': row.qty,
				'basic_rate': rate or 0,
				't_warehouse': 'Pallet In - %s' % abbr,
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
		doc.package_type = pkg.package_type
		doc.package_item = pkg.package_item
		doc.no_of_sheets = pkg.no_of_sheets
		doc.spools = cint(pkg.spools)
		doc.company = self.company
		doc.warehouse = row.warehouse

		if pkg.package_type == "Pallet":
			doc.is_returnable = pkg.is_returnable
			doc.returnable_by = pkg.returnable_by

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

def clear_package_weight(self):
	package_list = frappe.get_list("Package",filters={'purchase_document_type':self.doctype,'purchase_document_no':self.name})		
	for row in package_list:		
		doc = frappe.get_doc("Package", row.name)	
		if doc.status != "In Stock":
			frappe.throw(_("#Row {}: This Package is Partial Stock or Out of Stock.".format(row.idx)))

		#check_if_doc_is_linked(doc)
		#frappe.delete_doc("Package", doc.name)
		doc.net_weight = 0
		doc.gross_weight = 0
		doc.spool_weight = 0
		doc.tare_weight = 0
		doc.no_of_sheets = 0
		doc.save(ignore_permissions=True)

	# else:
		# frappe.db.commit()

def update_packages(self, method):
	if method == "on_submit" and self.is_return:
		for row in self.packages:
			package_no = frappe.db.get_value("Package",{'package_no':row.package,'purchase_document_no':self.return_against},'name')
			if not package_no:
				frappe.throw(_("Return Package not found"))
			doc = frappe.get_doc("Package", package_no)
			doc.add_consumption(self.doctype, self.name, row.net_weight, self.posting_date, self.posting_time)
			doc.save(ignore_permissions=True)

	elif method == "on_cancel" and self.is_return:
		for row in self.packages:
			package_no = frappe.db.get_value("Package",{'package_no':row.package,'purchase_document_no':self.return_against},'name')
			if not package_no:
				frappe.throw(_("Return Package not found"))
			doc = frappe.get_doc("Package", package_no)
			doc.remove_consumption(self.doctype, self.name)
			doc.save(ignore_permissions=True)

		
def update_pallet_item(self):
	count = 0
	if self.package_type == 'Pallet' and self.package_item:
		for d in self.packages:
			if d.package_item == self.package_item:
				count +=1
		if count > 0:
			if self.is_new() and not self.amended_from:				
				self.append("pallet_item",{
					'pallet_item': self.package_item,
					'qty': count
				})
			else:
				for d in self.packages:
					for r in self.pallet_item:
						if d.package_item == r.pallet_item:
							r.qty = count
							break


def add_package_consumption(self):
	if self.supplier_warehouse and self.supplied_items:
		for row in self.supplied_items:
			remaining_qty = row.required_qty
			package_list = frappe.get_list("Package", {
					'status': ["!=", "Out of Stock"],
					'item_code': row.rm_item_code,
					'batch_no': row.batch_no,
					'warehouse': self.supplier_warehouse,
				}, order_by = "creation DESC")

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
				
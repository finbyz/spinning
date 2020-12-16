from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt 

from frappe.model.mapper import get_mapped_doc
from erpnext.accounts.utils import get_fiscal_year
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from spinning.api import validate_inter_company_transaction, get_inter_company_details


def validate(self,method):
	hsn = self.items[0].gst_hsn_code
	for row in self.items:
		if row.gst_hsn_code != hsn:
			frappe.throw(_("Row: {} HSN code is different".format(row.idx)))
	calculate_gst_taxable_value(self)

def calculate_gst_taxable_value(self):
	account_list = []
	gst_setting = frappe.get_single("GST Settings")
	for row in gst_setting.gst_accounts:
		if row.company == self.company:
			account_list.append(row.cgst_account)
			account_list.append(row.sgst_account)
			account_list.append(row.igst_account)
			account_list.append(row.cess_account)
			account_list.append(row.tcs_account)
	for d in self.taxes:
		if d.account_head in account_list:
			self.gst_taxable_value = flt(d.base_total) - flt(d.base_tax_amount)
			break

#added

def on_submit(self, method):
	create_purchase_invoice(self)

def on_trash(self, method):
	delete_all(self)

def on_cancel(self, method):
	cancel_all(self)

def cancel_all(self):
	if self.get('pi_ref'):
		doc = frappe.get_doc("Purchase Invoice", self.pi_ref)

		if doc.docstatus == 1:
			doc.cancel()

def delete_all(self):
	if self.get('pr_ref'):
		pr_ref = self.pr_ref
		frappe.db.set_value("Purchase Invoice", self.pr_ref, 'inter_company_invoice_reference', None)
		frappe.db.set_value("Purchase Invoice", self.pr_ref, 'si_ref', None)

		self.db_set("pi_ref", None)
		self.db_set("inter_company_invoice_reference", None)
		
		doc = frappe.get_doc("Purchase Invoice", pi_ref)
		doc.delete()

	if self.get('pi_ref'):
		pi_ref = self.pi_ref
		frappe.db.set_value("Purchase Invoice", self.pi_ref, 'inter_company_invoice_reference', None)
		frappe.db.set_value("Purchase Invoice", self.pi_ref, 'si_ref', None)

		self.db_set("pi_ref", None)
		self.db_set("inter_company_invoice_reference", None)
		
		doc = frappe.get_doc("Purchase Invoice", pi_ref)
		doc.delete()

		

def create_purchase_invoice(self):
	check_inter_company_transaction = None

	if frappe.db.exists("Company",self.customer):
		check_inter_company_transaction = frappe.get_value(
			"Company", self.customer, "allow_inter_company_transaction"
		)
	
	if check_inter_company_transaction:
		
		company = frappe.get_doc("Company", self.customer)
		inter_company_list = [item.company for item in company.allowed_to_transact_with]
	
		if self.company in inter_company_list:
			pi = make_inter_company_transaction(self)

			for index, item in enumerate(self.items):
				if item.delivery_note:
					pi.items[index].purchase_receipt = frappe.db.get_value(
						"Delivery Note",
						item.delivery_note,
						'inter_company_receipt_reference'
					)

				if item.sales_order:
					pi.items[index].purchase_order = frappe.db.get_value(
						"Sales Order",
						item.sales_order,
						'inter_company_order_reference'
					)
		
			# authority = frappe.db.get_value("Company", pi.company, 'authority')
				
			# if authority == "Unauthorized" and (not pi.amended_from) and self.si_ref:
				
			# 	alternate_company = self.alternate_company
			# 	company_series = frappe.db.get_value("Company", alternate_company, 'company_series')

			# 	pi.company_series = frappe.db.get_value("Company", pi.name, "company_series")
			# 	pi.series_value = check_counter_series(pi.naming_series, company_series) - 1
			# 	pi.naming_series = 'A' + pi.naming_series
			
			pi.si_ref = self.name

			pi.save()
			if self.update_stock:
				pi.db_set('update_stock', 1)
			
			pi.submit()
			
			if self.si_ref:
				si_ref = frappe.db.get_value("Sales Invoice", self.name, 'si_ref')
				pi_ref = frappe.db.get_value("Sales Invoice", self.name, 'pi_ref')
				
				frappe.db.set_value("Purchase Invoice", pi.name, 'si_ref', self.name)
				frappe.db.set_value("Purchase Invoice", pi_ref, 'si_ref', si_ref)

			self.db_set('pi_ref', pi.name)

def make_inter_company_transaction(self, target_doc=None):
	source_doc  = frappe.get_doc("Sales Invoice", self.name)

	validate_inter_company_transaction(source_doc, "Sales Invoice")
	details = get_inter_company_details(source_doc, "Sales Invoice")

	def set_missing_values(source, target):
		if self.amended_from:
			name = frappe.db.get_value("Purchase Invoice", {'si_ref': self.amended_from}, "name")
			target.amended_from = name
		
		target.company = source.customer
		target.supplier = source.company
		# target.buying_price_list = source.selling_price_list
		target.posting_date = source.posting_date


		abbr = frappe.db.get_value("Company", target.company, 'abbr')

		target.set_warehouse = self.set_target_warehouse

		if source.taxes_and_charges:
			target_company_abbr = frappe.db.get_value("Company", target.company, "abbr")
			source_company_abbr = frappe.db.get_value("Company", source.company, "abbr")
			
			taxes_and_charges = source.taxes_and_charges.replace(
				source_company_abbr, target_company_abbr
			)

			if frappe.db.exists("Purchase Taxes and Charges Template", taxes_and_charges):
				target.taxes_and_charges = taxes_and_charges

			target.taxes = source.taxes
			
			for index, item in enumerate(source.taxes):
				target.taxes[index].account_head = item.account_head.replace(
					source_company_abbr, target_company_abbr
				)
			
		target.run_method("set_missing_values")
	
	def update_accounts(source_doc, target_doc, source_parent):
		target_company = source_parent.customer
		doc = frappe.get_doc("Company", target_company)

		if source_doc.pr_detail:
			target_doc.purchase_receipt = frappe.db.get_value("Purchase Receipt Item", source_doc.pr_detail, 'parent')
		if source_doc.purchase_order_item:
			target_doc.purchase_order = frappe.db.get_value("Purchase Order Item", source_doc.purchase_order_item, 'parent')

		target_doc.income_account = doc.default_income_account
		target_doc.expense_account = doc.default_expense_account
		target_doc.cost_center = doc.cost_center
	
	doclist = get_mapped_doc("Sales Invoice", self.name,	{
		"Sales Invoice": {
			"doctype": "Purchase Invoice",
			"field_map": {
				"name": "bill_no",
				"posting_date": "bill_date",
				"set_target_warehouse":"set_warehouse",
				"shipping_address_name": "shipping_address",
				"shipping_address": "shipping_address_display",
			},
			"field_no_map": [
				"taxes_and_charges",
				"series_value",
				"update_stock",
				"real_difference_amount"
			],
		},
		"Sales Invoice Item": {
			"doctype": "Purchase Invoice Item",
			"field_map": {
				"pr_detail": "pr_detail",
				"purchase_order_item": "po_detail",
			},
			"field_no_map": [
				"income_account",
				"expense_account",
				"cost_center",
				"warehouse",
			], "postprocess": update_accounts,
		}
	}, target_doc, set_missing_values)

	return doclist

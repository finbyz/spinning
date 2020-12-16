from __future__ import unicode_literals
import json
import frappe
from frappe import _
from frappe.utils import cstr, flt, cint, get_url_to_form
from six import string_types
from frappe.model.mapper import get_mapped_doc



def on_submit(self, method):
	create_sales_order(self)

def on_cancel(self, method):
	cancel_sales_order(self)

def on_trash(self, method):
	delete_sales_order(self)

def before_submit(self,method):
	item_dict = {}
	for row in self.items:
		row_index = item_dict.get((row.item_code+str(row.rate)), [])
		row_index.append(row.idx)
		item_dict.update({(row.item_code+str(row.rate)):row_index})
	
	for key, value in item_dict.items():
		if len(value) > 1:
			frappe.throw("Row:{0}: Not allowed to add multiple item with same rate.".format(value))
			
@frappe.whitelist()
def create_transfer(purchase_order, rm_items):
	if isinstance(rm_items, string_types):
		rm_items_list = json.loads(rm_items)
	else:
		frappe.throw(_("No Items available for transfer"))

	if rm_items_list:
		fg_items = list(set(d["item_code"] for d in rm_items_list))
	else:
		frappe.throw(_("No Items selected for transfer"))

	if purchase_order:
		purchase_order = frappe.get_doc("Purchase Order", purchase_order)

	if fg_items:
		items = tuple(set(d["rm_item_code"] for d in rm_items_list))
		item_wh = get_item_details(items)

		mt = frappe.new_doc("Material Transfer")
		mt.is_send_to_subcontractor = 1
		mt.purchase_order = purchase_order.name
		mt.supplier = purchase_order.supplier
		mt.supplier_name = purchase_order.supplier_name
		mt.address = purchase_order.address_display
		mt.company = purchase_order.company
		mt.t_warehouse = purchase_order.set_warehouse

		for item_code in fg_items:
			for rm_item_data in rm_items_list:
				if rm_item_data["item_code"] == item_code:
					rm_item_code = rm_item_data["rm_item_code"]
					
					items_dict = {
						rm_item_code: {
							"po_detail": rm_item_data.get("name"),
							"item_name": rm_item_data["item_name"],
							"description": item_wh.get(rm_item_code, {}).get('description', ""),
							'qty': rm_item_data["qty"],
							's_warehouse': purchase_order.set_warehouse,
							't_warehouse': purchase_order.supplier_warehouse,
							'stock_uom': rm_item_data["stock_uom"],
							'basic_rate':rm_item_data["rate"],
							'basic_amount':rm_item_data["amount"],
							'amount':rm_item_data["amount"],
							'main_item_code': rm_item_data["item_code"],
							'allow_alternative_item': item_wh.get(rm_item_code, {}).get('allow_alternative_item')
						}
					}
					mt.add_to_mt_detail(items_dict)
		return mt.as_dict()
	else:
		frappe.throw(_("No Items selected for transfer"))
	return purchase_order.name

def get_item_details(items):
	item_details = {}
	for d in frappe.db.sql("""select item_code, description, allow_alternative_item from `tabItem`
		where name in ({0})""".format(", ".join(["%s"] * len(items))), items, as_dict=1):
		item_details[d.item_code] = d

	return item_details


# For Intercompany transaction
def create_sales_order(self):
	def get_sales_order_entry(source_name, target_doc=None, ignore_permissions= True):
		def set_missing_value(source, target):
			target.company = source.supplier
			target.customer = source.company

			target_company_abbr = frappe.db.get_value("Company", target.company, "abbr")
			source_company_abbr = frappe.db.get_value("Company", source.company, "abbr")

			if source.taxes_and_charges:
				target_taxes_and_charges = source.taxes_and_charges.replace(source_company_abbr, target_company_abbr)
				if frappe.db.exists("Sales Taxes and Charges Template", target_taxes_and_charges):
					target.taxes_and_charges = target_taxes_and_charges

			if self.amended_from:
				name = frappe.db.get_value("Sales Order", {'po_ref': self.amended_from}, "name")
				target.amended_from = name
			
			target.transaction_date = source.transaction_date
			target.set_posting_time = 1

			target.run_method("set_missing_values")
			target.run_method("calculate_taxes_and_charges")

		def update_items(source_doc, target_doc, source_parent):
			source_company_abbr = frappe.db.get_value("Company", source_parent.company, "abbr")
			target_company_abbr = frappe.db.get_value("Company", source_parent.supplier, "abbr")

			if source_doc.warehouse:
				# target_doc.warehouse = source_doc.warehouse.replace(source_company_abbr, target_company_abbr)
				target_doc.warehouse = self.set_supplier_warehouse


		def update_taxes(source_doc, target_doc, source_parent):
			source_company_abbr = frappe.db.get_value("Company", source_parent.company, "abbr")
			target_company_abbr = frappe.db.get_value("Company", source_parent.supplier, "abbr")

			if source_doc.account_head:
				target_doc.account_head = source_doc.account_head.replace(source_company_abbr, target_company_abbr)

			if source_doc.cost_center:
				target_doc.cost_center = source_doc.cost_center.replace(source_company_abbr, target_company_abbr)

		fields = {
			"Purchase Order": {
				"doctype": "Sales Order",
				"field_map": {
					"schedule_date": "delivery_date",
					"name": "po_ref",
					"transaction_date": "po_date",
					"buying_price_list": "selling_price_list",
				},
				"field_no_map": [
					"taxes_and_charges",
					"series_value",
					"set_warehouse"
				]
			},
			"Purchase Order Item": {
				"doctype": "Sales Order Item",
				"field_map": {
					"name": "purchase_order_item",
				},
				"field_no_map": [
					"warehouse",
					"cost_center",
					"expense_account",
					"income_account",
				],
				"postprocess": update_items,
			},
			"Purchase Taxes and Charges": {
				"doctype": "Sales Taxes and Charges",
				"postprocess": update_taxes,
			}
		}

		doc = get_mapped_doc(
			"Purchase Order",
			source_name,
			fields,
			target_doc,
			set_missing_value,
			ignore_permissions=ignore_permissions
		)

		return doc

	check_inter_company_transaction = frappe.get_value("Company", self.company, "allow_inter_company_transaction")
	if check_inter_company_transaction:
		company = frappe.get_doc("Company", self.company)
		inter_company_list = [item.company for item in company.allowed_to_transact_with]
		supplier_company = frappe.db.get_value("Supplier",self.supplier,'represents_company')
		if supplier_company in inter_company_list:
			# price_list = self.buying_price_list
			# if price_list:
			# 	valid_price_list = frappe.db.get_value("Price List", {"name": price_list, "buying": 1, "selling": 1})
			# else:
			# 	frappe.throw(_("Selected Price List should have buying and selling fields checked."))

			# if not valid_price_list:
			# 	frappe.throw(_("Selected Price List should have buying and selling fields checked."))
			so = get_sales_order_entry(self.name)

			so.save(ignore_permissions = True)
			so.submit()


			self.db_set('order_confirmation_no', so.name)
			self.db_set('order_confirmation_date', so.transaction_date)
			self.db_set('inter_company_order_reference', so.name)
			self.db_set('so_ref', so.name)

			so.db_set('inter_company_order_reference', self.name)
			so.db_set('po_no', self.name)

			url = get_url_to_form("Sales Order", so.name)

			frappe.msgprint(_("Sales Order <b><a href='{url}'>{name}</a></b> has been created successfully!".format(url=url, name=so.name)), title="Sales Order Created", indicator="green")


def cancel_sales_order(self):
	if self.so_ref:
		so = frappe.get_doc("Sales Order", self.so_ref)
		so.flags.ignore_permissions = True
		if so.docstatus == 1:
			so.cancel()

		url = get_url_to_form("Sales Order", so.name)
		frappe.msgprint(_("Sales Order <b><a href='{url}'>{name}</a></b> has been cancelled!".format(url=url, name=so.name)), title="Sales Order Cancelled", indicator="red")

def delete_sales_order(self):
	if self.so_ref:
		frappe.db.set_value("Purchase Order", self.name, 'inter_company_order_reference', '')
		frappe.db.set_value("Purchase Order", self.name, 'so_ref', '')

		frappe.db.set_value("Sales Order", self.so_ref, 'po_ref', '')

		if frappe.db.exists("Sales Order", self.so_ref):
			frappe.delete_doc("Sales Order", self.so_ref, force = 1, ignore_permissions=True)
			frappe.msgprint(_("Sales Order <b>{name}</b> has been deleted!".format(name=self.so_ref)), title="Sales Order Deleted", indicator="red")

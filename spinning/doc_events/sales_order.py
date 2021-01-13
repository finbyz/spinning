import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt
from frappe.model.utils import get_fetch_values

@frappe.whitelist()
def make_delivery_note(source_name, target_doc=None, skip_item_mapping = False):
	def set_missing_values(source, target):
		target.ignore_pricing_rule = 1
		target.run_method("set_missing_values")
		target.run_method("set_po_nos")
		target.run_method("calculate_taxes_and_totals")

		if source.company_address:
			target.update({'company_address': source.company_address})
		else:
			# set company address
			target.update(get_company_address(target.company))

		if target.company_address:
			target.update(get_fetch_values("Delivery Note", 'company_address', target.company_address))

	def update_item(source, target, source_parent):
		if not skip_item_mapping:
			for i in source.items:
				if frappe.db.get_value("Item", i.item_code, 'is_stock_item'):
					for j in frappe.get_all("Pick List Item", filters={"sales_order": source.name, "sales_order_item": i.name, "docstatus": 1}):
						pick_doc = frappe.get_doc("Pick List Item", j.name)
						
						if pick_doc.qty - pick_doc.delivered_qty > 0:
							target.append('items',{
								'item_code': pick_doc.item_code,
								'qty': pick_doc.qty - pick_doc.delivered_qty,
								'rate': i.rate,
								'against_sales_order': source.name,
								'so_detail': i.name,
								'purchase_order_item':i.purchase_order_item,
								'pick_list_no': pick_doc.parent,
								'against_pick_list': pick_doc.name,
								'warehouse': pick_doc.warehouse,
								'batch_no': pick_doc.batch_no,
								'merge': pick_doc.merge,
								'grade': pick_doc.grade,
								'picked_qty': pick_doc.qty - pick_doc.delivered_qty
							})
				else:
					target.append('items',{
						'item_code': i.item_code,
						'qty': i.qty,
						'rate': i.rate,
						'against_sales_order': source.name,
						'so_detail': i.name,
						'purchase_order_item':i.purchase_order_item,
						'warehouse': i.warehouse,
						'item_series': i.item_series
					})

	mapper = {
		"Sales Order": {
			"doctype": "Delivery Note",
			"validation": {
				"docstatus": ["=", 1]
			},
			"postprocess": update_item
		},
		"Sales Taxes and Charges": {
			"doctype": "Sales Taxes and Charges",
			"add_if_empty": True
		},
		"Sales Team": {
			"doctype": "Sales Team",
			"add_if_empty": True
		}
	}

	target_doc = get_mapped_doc("Sales Order", source_name, mapper, target_doc, set_missing_values)
	
	return target_doc

@frappe.whitelist()
def create_pick_list(source_name, target_doc=None):
	def update_item_quantity(source, target, source_parent):
		target.qty = flt(source.qty) - flt(source.picked_qty)
		target.so_qty = flt(source.qty)
		target.stock_qty = (flt(source.qty) - flt(source.picked_qty)) * flt(source.conversion_factor)
		target.picked_qty = source.picked_qty
		target.remaining_qty = target.so_qty - target.qty - target.picked_qty
		target.customer = source_parent.customer
		target.date = source_parent.transaction_date
		target.delivery_date = source.delivery_date

	doc = get_mapped_doc('Sales Order', source_name, {
		'Sales Order': {
			'doctype': 'Pick List',
			'field_map': {
				'delivery_date': 'delivery_date'
			},
			'validation': {
				'docstatus': ['=', 1],
			}
		},
		'Sales Order Item': {
			'doctype': 'Pick List Item',
			'field_map': {
				'parent': 'sales_order',
				'name': 'sales_order_item',
			},
			'field_no_map': [
				'warehouse'
			],
			'postprocess': update_item_quantity,
			'condition': lambda doc: abs(doc.picked_qty) < abs(doc.qty) and doc.delivered_by_supplier!=1
		},
	}, target_doc)

	doc.purpose = 'Delivery'
	# doc.delivery_date = frappe.db.get_value('Sales Order', source_name, 'delivery_date')
	doc.set_item_locations()
	return doc

def before_submit(self,method):
	item_dict = {}
	for row in self.items:
		row_index = item_dict.get((row.item_code+str(row.rate)), [])
		row_index.append(row.idx)
		item_dict.update({(row.item_code+str(row.rate)):row_index})
	
	for key, value in item_dict.items():
		if len(value) > 1:
			frappe.throw("Row:{0}: Not allowed to add multiple item with same rate.".format(value))
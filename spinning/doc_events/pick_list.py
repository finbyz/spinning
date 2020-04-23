import frappe
from frappe import _
from frappe.utils import today
from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note as create_delivery_note_from_sales_order
from frappe.model.mapper import get_mapped_doc, map_child_doc


def validate(self, method):
	pass

def before_submit(self, method):
	check = []
	for item in self.locations:
		if item.qty != item.picked_qty:
			frappe.throw("Row: {} Quantity is not same as picked quantity.".format(item.idx))
		else:
			flag = False
			for item2 in check:
				if item2.get('item_code') == item.item_code and item2.get('warehouse') == item.warehouse and item2.get('batch_no') == item.batch_no:
					item2['qty'] = (item2.get('qty') or  0.0) + item.qty
					flag = True
					break

			if not flag:
				check.append({
					'item_code': item.item_code,
					'warehouse': item.warehouse,
					'merge': item.merge,
					'grade': item.grade,
					'qty': item.qty,
					'batch_no': item.batch_no,
				})

	for item in check:
		# frappe.msgprint(str(check_item_qty(item['item_code'], item['warehouse'], item['qty'], item['batch_no'], self.company)))
		if check_item_qty(item['item_code'], item['warehouse'], item['qty'], item['batch_no'], self.company) < 0:
			frappe.throw("Qty Not Availabe to pick for item {} for merge {} and grade {}".format(item['item_code'], item['merge'], item['grade']))

def on_submit(self, method):
	update_sales_order(self, 'submit')

def update_sales_order(self, method):
	if method == "submit":
		for item in self.locations:
			tile = frappe.get_doc("Sales Order Item", {'name': item.sales_order_item, 'parent': item.sales_order})
			picked_qty = tile.picked_qty + item.qty
			if picked_qty > tile.qty:
				frappe.throw("Can not pick item {} in row {} more than {}".format(item.item_code, item.idx, item.qty - item.picked_qty))

			tile.db_set('picked_qty', picked_qty)
	
	if method == "cancel":
		for item in self.locations:
			tile = frappe.get_doc("Sales Order Item", {'name': item.sales_order_item, 'parent': item.sales_order})
			picked_qty = tile.picked_qty - item.qty

			if tile.picked_qty < 0:
				frappe.throw("Row {}: All Item Already Canclled".format(item.idx))

			tile.db_set('picked_qty', picked_qty)

def on_cancel(self, method):
	update_sales_order(self, 'cancel')

def before_save(self, method):
	for item in self.locations:
		item.picked_qty = item.qty

@frappe.whitelist()
def get_items(filters):
	from six import string_types
	import json

	if isinstance(filters, string_types):
		filters = json.loads(filters)
		
	warehouse_condition = ''
	batch_locations = frappe.db.sql("""
		SELECT
			sle.`item_code`,
			sle.`warehouse`,
			sle.`batch_no`,
			SUM(sle.`actual_qty`) AS `actual_qty`,
			batch.`grade`, batch.`merge`
		FROM
			`tabStock Ledger Entry` sle, `tabBatch` batch
			
		WHERE
			sle.batch_no = batch.name
			and sle.`item_code`=%(item_code)s
			and sle.`company` = '{company}'
			and IFNULL(batch.`expiry_date`, '2200-01-01') > %(today)s
			{warehouse_condition}
		GROUP BY
			`warehouse`,
			`batch_no`,
			`item_code`
		HAVING `actual_qty` > 0
		ORDER BY IFNULL(batch.`expiry_date`, '2200-01-01'), batch.`creation`
	""".format(warehouse_condition=warehouse_condition, company=filters['company']), { #nosec
		'item_code': filters['item_code'],
		'today': today(),
	}, as_dict=1)

	item_name = frappe.db.get_value('Item', filters['item_code'], 'item_name')
	
	data = []
	for item in batch_locations:
		item['item_name'] = item_name
		
		pick_list_available = frappe.db.sql(f"""
			SELECT SUM(pli.qty - pli.delivered_qty) FROM `tabPick List Item` as pli
			JOIN `tabPick List` AS pl ON pl.name = pli.parent
			WHERE `item_code` = '{filters['item_code']}'
			AND warehouse = '{item['warehouse']}'
			AND batch_no = '{item['batch_no']}'
			AND pl.docstatus = 1
		""")

		item['available_qty'] = item['actual_qty'] - (pick_list_available[0][0] or 0.0)
		item['picked_qty'] = item['available_qty']
		item['to_pick_qty'] = str(item['available_qty'])
		if item:
			data.append(item)
	
	return data

def check_item_qty(item_code, warehouse, qty, batch_no, company):
	batch_locations = frappe.db.sql(f"""
		SELECT
			SUM(sle.`actual_qty`) AS `actual_qty`
		FROM
			`tabStock Ledger Entry` sle, `tabBatch` batch
		WHERE
			sle.batch_no = batch.name
			and sle.`item_code`='{item_code}'
			and sle.`warehouse`='{warehouse}'
			and sle.`batch_no`='{batch_no}'
			and sle.`company` = '{company}'
			and IFNULL(batch.`expiry_date`, '2200-01-01') > '{today()}'
		GROUP BY
			`warehouse`,
			`batch_no`,
			`item_code`
		HAVING `actual_qty` > 0
		ORDER BY IFNULL(batch.`expiry_date`, '2200-01-01'), batch.`creation`
	""")[0][0] or 0.0

	pick_list_available = frappe.db.sql(f"""
		SELECT SUM(pli.qty - pli.delivered_qty) FROM `tabPick List Item` as pli
		JOIN `tabPick List` AS pl ON pl.name = pli.parent
		WHERE pli.`item_code` = '{item_code}'
		AND pli.warehouse = '{warehouse}'
		AND pli.batch_no = '{batch_no}'
		AND pl.docstatus = 1
	""")[0][0] or 0.0

	# frappe.throw(str(pick_list_available2))

	return (batch_locations - pick_list_available) - qty

@frappe.whitelist()
def create_delivery_note(source_name, target_doc=None):
	pick_list = frappe.get_doc('Pick List', source_name)
	sales_orders = [d.sales_order for d in pick_list.locations]
	sales_orders = set(sales_orders)

	delivery_note = None
	for sales_order in sales_orders:
		delivery_note = create_delivery_note_from_sales_order(sales_order,
			delivery_note, skip_item_mapping=True)

	item_table_mapper = {
		'doctype': 'Delivery Note Item',
		'field_map': {
			'rate': 'rate',
			'name': 'so_detail',
			'parent': 'against_sales_order',
		},
		'condition': lambda doc: abs(doc.delivered_qty) < abs(doc.qty) and doc.delivered_by_supplier!=1
	}

	for location in pick_list.locations:
		sales_order_item = frappe.get_cached_doc('Sales Order Item', location.sales_order_item)
		dn_item = map_child_doc(sales_order_item, delivery_note, item_table_mapper)

		if dn_item:
			dn_item.warehouse = location.warehouse
			dn_item.qty = location.picked_qty
			dn_item.batch_no = location.batch_no
			dn_item.serial_no = location.serial_no

			dn_item.against_pick_list = location.name
			dn_item.pick_list = pick_list.name
			dn_item.picked_qty = location.picked_qty

			dn_item.merge = location.merge
			dn_item.grade = location.grade
			dn_item.picked_qty = location.picked_qty
			update_delivery_note_item(sales_order_item, dn_item, delivery_note)

	set_delivery_note_missing_values(delivery_note)

	return delivery_note

def update_delivery_note_item(source, target, delivery_note):
	cost_center = frappe.db.get_value('Project', delivery_note.project, 'cost_center')
	if not cost_center:
		cost_center = get_cost_center(source.item_code, 'Item', delivery_note.company)

	if not cost_center:
		cost_center = get_cost_center(source.item_group, 'Item Group', delivery_note.company)

	target.cost_center = cost_center

def get_cost_center(for_item, from_doctype, company):
	'''Returns Cost Center for Item or Item Group'''
	return frappe.db.get_value('Item Default',
		fieldname=['buying_cost_center'],
		filters={
			'parent': for_item,
			'parenttype': from_doctype,
			'company': company
		})

def set_delivery_note_missing_values(target):
	target.run_method('set_missing_values')
	target.run_method('set_po_nos')
	target.run_method('calculate_taxes_and_totals')

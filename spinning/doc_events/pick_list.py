import frappe
from frappe import _

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
			SUM(sle.`actual_qty`) AS `actual_qty`
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
			SELECT SUM(pli.picked_qty - pli.delivered_qty) FROM `tabPick List Item` as pli
			JOIN `tabPick List` AS pl ON pl.name = pli.parent
			WHERE `item_code` = '{filters['item_code']}'
			AND warehouse = '{item['warehouse']}'
			AND batch_no = '{item['batch_no']}'
			AND pl.docstatus = 1
		""")

		item['available_qty'] = item['actual_qty'] - (pick_list_available[0][0] or 0.0)
		if item['available_qty'] <= 0.0:
			item = None
		del item['actual_qty']
		item['picked_qty'] = item['available_qty']

		if item:
			data.append(item)
	
	return data
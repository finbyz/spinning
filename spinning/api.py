# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint, cstr
from frappe.desk.reportview import get_match_cond

	
# @frappe.whitelist()
# def override_bom_autoname(self,method):
# 	from erpnext.manufacturing.doctype.bom.bom import BOM
# 	BOM.autoname = bom_autoname
	
# def bom_autoname(self):
# 	self.name = 'BOM-' + self.merge + "-" + self.item


# @frappe.whitelist()
# def pi_validate(self, method):
# 	if self.update_stock:
# 		set_batches(self, 'warehouse')

# @frappe.whitelist()
# def stock_entry_validate(self, method):
# 	if self._action == 'submit':
# 		set_batches(self, 't_warehouse')
# 	else:
# 		validate_batch_details(self)

# 	if self.purpose in ["Repack", "Manufacture"]:
# 		self.run_method("get_stock_and_rate")

# def validate_batch_details(self):
# 	wo_merge = None

# 	if self.get('work_order'):
# 		wo_merge = frappe.db.get_value("Work Order", self.work_order, 'merge')
	
# 	for row in self.items:
# 		has_batch_no = frappe.db.get_value('Item', row.item_code, 'has_batch_no')

# 		if has_batch_no:
# 			if row.s_warehouse and row.batch_no:
# 				row.merge, row.grade = frappe.db.get_value("Batch", row.batch_no, ['merge', 'grade'])

# 			elif row.t_warehouse and wo_merge and row.merge != wo_merge:
# 				frappe.throw(_("#Row {}: Merge should be same as Work Order Merge!".format(row.idx)))

# def set_batches(self, warehouse_field):
# 	if self._action == 'submit':
# 		for row in self.items:
# 			if not row.get(warehouse_field):
# 				continue

# 			has_batch_no = frappe.db.get_value('Item', row.item_code, 'has_batch_no')

# 			if has_batch_no:
# 				if not row.get('merge'):
# 					frappe.throw(_("Please set Merge in row {}".format(row.idx)))

# 				if not row.get('grade'):
# 					frappe.throw(_("Please set Grade in row {}".format(row.idx)))

# 				batch_nos = frappe.db.sql_list(""" select name from `tabBatch` 
# 					where grade = %s and merge = %s and item = %s """, (row.grade, row.merge, row.item_code))

# 				if batch_nos:
# 					row.batch_no = batch_nos[0]

# 				else:
# 					batch = frappe.new_doc("Batch")
# 					batch.item = row.item_code
# 					batch.supplier = getattr(self, 'supplier', None)
# 					batch.packaging_material = cstr(row.packaging_material)
# 					batch.packing_size = cstr(row.packing_size)
# 					batch.grade = cstr(row.grade)
# 					batch.merge = cstr(row.merge)
# 					batch.reference_doctype = self.doctype
# 					batch.reference_name = self.name
# 					batch.insert()
# 					row.batch_no = batch.name

# 			elif row.grade or row.merge:
# 				frappe.throw(_("Please clear Grade and Merge for Item {} as it is not batch wise item in row {}".format(row.item_code, row.idx)))

def get_batch_no(doctype, txt, searchfield, start, page_len, filters):
	cond = ""

	meta = frappe.get_meta("Batch")
	searchfield = meta.get_search_fields()

	searchfields = " or ".join(["batch." + field + " like %(txt)s" for field in searchfield])

	if filters.get("posting_date"):
		cond = "and (batch.expiry_date is null or batch.expiry_date >= %(posting_date)s)"

	batch_nos = None
	args = {
		'item_code': filters.get("item_code"),
		'warehouse': filters.get("warehouse"),
		'posting_date': filters.get('posting_date'),
		'txt': "%{0}%".format(txt),
		"start": start,
		"page_len": page_len
	}

	if args.get('warehouse'):
		batch_nos = frappe.db.sql("""select sle.batch_no, batch.grade, batch.merge, round(sum(sle.actual_qty),2), sle.stock_uom
				from `tabStock Ledger Entry` sle
				    INNER JOIN `tabBatch` batch on sle.batch_no = batch.name
				where
					sle.item_code = %(item_code)s
					and sle.warehouse = %(warehouse)s
					and batch.docstatus < 2
					and (sle.batch_no like %(txt)s or {searchfields})
					{0}
					{match_conditions}
				group by batch_no having sum(sle.actual_qty) > 0
				order by batch.expiry_date, sle.batch_no desc
				limit %(start)s, %(page_len)s""".format(cond, match_conditions=get_match_cond(doctype), searchfields=searchfields), args)

	if batch_nos:
		return batch_nos
	else:
		return frappe.db.sql("""select name, grade, merge, expiry_date from `tabBatch` batch
			where item = %(item_code)s
			and name like %(txt)s
			and docstatus < 2
			{0}
			{match_conditions}
			order by expiry_date, name desc
			limit %(start)s, %(page_len)s""".format(cond, match_conditions=get_match_cond(doctype)), args)


@frappe.whitelist()
def make_stock_entry(work_order_id, purpose, qty=None):
	from erpnext.stock.doctype.stock_entry.stock_entry import get_additional_costs

	work_order = frappe.get_doc("Work Order", work_order_id)
	if not frappe.db.get_value("Warehouse", work_order.wip_warehouse, "is_group") \
			and not work_order.skip_transfer:
		wip_warehouse = work_order.wip_warehouse
	else:
		wip_warehouse = None

	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.purpose = purpose
	stock_entry.work_order = work_order_id
	stock_entry.company = work_order.company
	stock_entry.from_bom = 1
	stock_entry.bom_no = work_order.bom_no
	stock_entry.use_multi_level_bom = work_order.use_multi_level_bom
	stock_entry.fg_completed_qty = qty or (flt(work_order.qty) - flt(work_order.produced_qty))
	if work_order.bom_no:
		stock_entry.inspection_required = frappe.db.get_value('BOM',
			work_order.bom_no, 'inspection_required')

	if purpose=="Material Transfer for Manufacture":
		stock_entry.to_warehouse = wip_warehouse
		stock_entry.project = work_order.project
	else:
		stock_entry.from_warehouse = wip_warehouse
		stock_entry.to_warehouse = work_order.fg_warehouse
		stock_entry.project = work_order.project
		if purpose=="Manufacture":
			additional_costs = get_additional_costs(work_order, fg_qty=stock_entry.fg_completed_qty)
			stock_entry.set("additional_costs", additional_costs)

	stock_entry.get_items()

	if purpose == "Manufacture":
		stock_entry.items[-1].merge = work_order.merge

	return stock_entry.as_dict()

@frappe.whitelist()
def make_workorder_finish(work_order_id):
	work_order = frappe.get_doc("Work Order", work_order_id)
	
	wof = frappe.new_doc("Work Order Finish")
	wof.work_order = work_order_id
	wof.company = work_order.company
	wof.item_code = work_order.production_item
	wof.merge = work_order.merge
	wof.package_type = work_order.package_type
	wof.is_returnable = work_order.is_returnable
	wof.fg_completed_qty = work_order.qty
	wof.spool_color = work_order.spool_color
	wof.spool_weight = work_order.spool_weight
	wof.target_warehouse = work_order.fg_warehouse
	
	return wof

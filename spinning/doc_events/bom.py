# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint, cstr, flt

@frappe.whitelist()
def before_naming(self, method):
	override_bom_autoname(self)

def override_bom_autoname(self):
	from erpnext.manufacturing.doctype.bom.bom import BOM
	BOM.autoname = bom_autoname

def bom_autoname(self):
	self.name = 'BOM-' + self.merge + "-" + self.item
	
def on_submit(self, method):
	for row in self.items:
		has_batch_no = frappe.db.get_value('Item', row.item_code, 'has_batch_no')
		if has_batch_no:
			if not row.get('merge'):
				frappe.throw(_("Please set Merge in row {}").format(row.idx))

def get_bom_items_as_dict(bom, company, qty=1, fetch_exploded=1, fetch_scrap_items=0, include_non_stock_items=False, fetch_qty_in_stock_uom=True):
	item_dict = {}

	# Did not use qty_consumed_per_unit in the query, as it leads to rounding loss
	# Finbyz CHanges START: Removed group by and sum fo qty
	query = """select
				bom_item.item_code,
				bom_item.idx,
				item.item_name,
				bom_item.{qty_field}/ifnull(bom.quantity, 1) * %(qty)s as qty,
				item.image,
				bom.project,
				item.stock_uom,
				item.allow_alternative_item,
				item_default.default_warehouse,
				item_default.expense_account as expense_account,
				item_default.buying_cost_center as cost_center
				{select_columns}
			from
				`tab{table}` bom_item
				JOIN `tabBOM` bom ON bom_item.parent = bom.name
				JOIN `tabItem` item ON item.name = bom_item.item_code
				LEFT JOIN `tabItem Default` item_default
					ON item_default.parent = item.name and item_default.company = %(company)s
			where
				bom_item.docstatus < 2
				and bom.name = %(bom)s
				and item.is_stock_item in (1, {is_stock_item})
				{where_conditions}
				order by idx"""
	# Finbyz CHanges END
	is_stock_item = 0 if include_non_stock_items else 1
	if cint(fetch_exploded):
		query = query.format(table="BOM Explosion Item",
			where_conditions="",
			is_stock_item=is_stock_item,
			qty_field="stock_qty",
			select_columns = """, bom_item.source_warehouse, bom_item.operation,
				bom_item.include_item_in_manufacturing, bom_item.description, bom_item.rate,
				(Select idx from `tabBOM Item` where item_code = bom_item.item_code and parent = %(parent)s limit 1) as idx""")

		items = frappe.db.sql(query, { "parent": bom, "qty": qty, "bom": bom, "company": company }, as_dict=True)
	elif fetch_scrap_items:
		query = query.format(table="BOM Scrap Item", where_conditions="",
			select_columns=", bom_item.idx, item.description", is_stock_item=is_stock_item, qty_field="stock_qty")

		items = frappe.db.sql(query, { "qty": qty, "bom": bom, "company": company }, as_dict=True)
	else:
		#Finbyz Changes START: bom_item.merge selected
		query = query.format(table="BOM Item", where_conditions="", is_stock_item=is_stock_item,
			qty_field="stock_qty" if fetch_qty_in_stock_uom else "qty",
			select_columns = """, bom_item.uom, bom_item.conversion_factor, bom_item.source_warehouse,bom_item.merge,
				bom_item.idx, bom_item.operation, bom_item.include_item_in_manufacturing,
				bom_item.description, bom_item.base_rate as rate """)
		#Finbyz Changes END
		items = frappe.db.sql(query, { "qty": qty, "bom": bom, "company": company }, as_dict=True)

	#Finbyz Changes START
	for item in items:
		if cint(fetch_exploded) or fetch_scrap_items:
			if item.item_code in item_dict:
				item_dict[item.item_code]["qty"] += flt(item.qty)
			else:
				item_dict[item.item_code] = item
		else:
			if item.item_code in item_dict:
				if item.get('merge'):
					item_dict[item.item_code + item.merge]["qty"] += flt(item.qty)
				else:
					item_dict[item.item_code]["qty"] += flt(item.qty)
			else:
				if item.get('merge'):
					item_dict[item.item_code + item.merge] = item
				else:
					item_dict[item.item_code] = item
	# Finbyz CHanges END	

	for item, item_details in item_dict.items():
		for d in [["Account", "expense_account", "stock_adjustment_account"],
			["Cost Center", "cost_center", "cost_center"], ["Warehouse", "default_warehouse", ""]]:
				company_in_record = frappe.db.get_value(d[0], item_details.get(d[1]), "company")
				if not item_details.get(d[1]) or (company_in_record and company != company_in_record):
					item_dict[item][d[1]] = frappe.get_cached_value('Company',  company,  d[2]) if d[2] else None

	return item_dict
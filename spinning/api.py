# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, cint
from frappe.contacts.doctype.address.address import get_company_address
from erpnext.accounts.utils import get_fiscal_year, getdate
import datetime

@frappe.whitelist()
def company_address(company):
	return get_company_address(company)

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
	wof.package_item = work_order.package_item
	wof.is_returnable = work_order.is_returnable
	wof.fg_completed_qty = work_order.qty
	wof.paper_tube = work_order.paper_tube
	wof.spool_weight = work_order.spool_weight
	wof.target_warehouse = work_order.fg_warehouse
	wof.source_warehouse = work_order.source_warehouse
	wof.workstation = work_order.workstation
	# wof.series = work_order.series
	
	return wof

@frappe.whitelist()
def get_merge_wise_package_details(batch_no, warehouse):
	return frappe.get_list("Package", filters={
		'batch_no': batch_no, 
		'warehouse': warehouse, 
		'status': ['!=', "Out of Stock"]
	}, fields = ['package_no', 'name', 'package_type', 'gross_weight', 'net_weight', 'spools', 'remaining_qty', 'status'])

@frappe.whitelist()
def get_package_details(batch_no,to_date):
	sql = frappe.db.sql("""
	SELECT p.package_no, p.name, p.package_type, p.spools, p.gross_weight, p.net_weight, (p.net_weight - sum(IFNULL(case when pc.posting_date <= '{0}' then pc.consumed_qty end,0))) as remaining
		FROM `tabPackage` as p
		LEFT JOIN `tabPackage Consumption` as pc ON pc.parent = p.name
		WHERE 
			p.purchase_date <= '{0}' and p.batch_no = '{1}'
		GROUP BY p.name
		HAVING remaining > 0
	""".format(to_date, batch_no))

	return sql
	
	# return frappe.get_list("Package", filters={
	# 	'batch_no': batch_no,
	# 	'status': ['!=', "Out of Stock"]
	# }, fields = ['name', 'package_type', 'gross_weight', 'net_weight', 'spools', 'remaining_qty', 'status'])
	
@frappe.whitelist()
def before_naming(self, method):
	if not self.get('amended_from') and not self.get('name'):
		date = self.get("transaction_date") or self.get("posting_date") or  self.get("manufacturing_date") or getdate()
		fiscal = get_fiscal(date)
		self.fiscal = fiscal
		if not self.get('company_series'):
			self.company_series = None
		if self.get('series_value'):
			if self.series_value > 0:
				name = naming_series_name(self.naming_series, fiscal, self.company_series)
				check = frappe.db.get_value('Series', name, 'current', order_by="name")
				if check == 0:
					pass
				elif not check:
					frappe.db.sql("insert into tabSeries (name, current) values ('{}', 0)".format(name))

				frappe.db.sql("update `tabSeries` set current = {} where name = '{}'".format(cint(self.series_value) - 1, name))

def naming_series_name(name, fiscal, company_series=None):
	if company_series:
		name = name.replace('company_series', str(company_series))
	
	name = name.replace('YYYY', str(datetime.date.today().year))
	name = name.replace('YY', str(datetime.date.today().year)[2:])
	name = name.replace('MM', f'{datetime.date.today().month:02d}')
	name = name.replace('DD', f'{datetime.date.today().day:02d}')
	name = name.replace('fiscal', str(fiscal))
	name = name.replace('#',	'')
	name = name.replace('.', '')
	
	return name

@frappe.whitelist()
def get_fiscal(date):
	fy = get_fiscal_year(date)[0]
	fiscal = frappe.db.get_value("Fiscal Year", fy, 'fiscal')

	return fiscal if fiscal else fy.split("-")[0][2:] + fy.split("-")[1][2:]


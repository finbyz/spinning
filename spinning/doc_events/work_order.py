# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint, cstr, flt

from erpnext.manufacturing.doctype.work_order.work_order import WorkOrder
from spinning.doc_events.bom import get_bom_items_as_dict 

class StockOverProductionError(frappe.ValidationError): pass


@frappe.whitelist()
def update_work_order_status(doc, qty):
	wo = frappe.get_doc("Work Order", doc)

	if wo.status != "In Process":
		wo.db_set("status", "In Process")

	manufacturing_start_qty = flt(qty) + flt(wo.manufacturing_start_qty)

	wo.db_set('manufacturing_start_qty', flt(manufacturing_start_qty))

def override_work_order_functions():
	WorkOrder.update_work_order_qty = update_work_order_qty

def update_work_order_qty(self):
	"""Update **Manufactured Qty** and **Material Transferred for Qty** in Work Order
			based on Stock Entry"""

	allowance_percentage = flt(frappe.db.get_single_value("Manufacturing Settings",
		"overproduction_percentage_for_work_order"))

	purpose = "Manufacture"
	fieldname = "produced_qty"

	qty = flt(frappe.db.sql("""select sum(fg_completed_qty)
		from `tabStock Entry` where work_order=%s and docstatus=1
		and purpose=%s""", (self.name, purpose))[0][0])

	completed_qty = self.qty + (allowance_percentage/100 * self.qty)
	if qty > completed_qty:
		frappe.throw(_("{0} ({1}) cannot be greater than planned quantity ({2}) in Work Order {3}").format(\
			self.meta.get_label(fieldname), qty, completed_qty, self.name), StockOverProductionError)

	self.db_set(fieldname, qty)

	if self.production_plan:
		self.update_production_plan_status()

def before_save(self, method):
	self.manufacturing_start_qty = 0
	#update_merge(self)
	
def update_merge(self):
	if self.bom_no:
		bom = frappe.get_doc("BOM",self.bom_no)
		for wo_item in self.required_items:
			for bom_item in bom.items:
				if wo_item.item_code == bom_item.item_code:
					wo_item.merge = bom_item.merge

def on_submit(self,method):
	if self.paper_tube and not self.spool_weight:
		frappe.throw(_("Please set Weight per unit in {}").format(self.paper_tube))

@frappe.whitelist()	
def sales_order_query(doctype, txt, searchfield, start, page_len, filters):
	conditions = []

	so_searchfield = frappe.get_meta("Sales Order").get_search_fields()
	so_searchfields = " or ".join(["so.`" + field + "` like %(txt)s" for field in so_searchfield])

	soi_searchfield = frappe.get_meta("Sales Order Item").get_search_fields()
	soi_searchfield += ["item_code"]
	soi_searchfields = " or ".join(["soi.`" + field + "` like %(txt)s" for field in soi_searchfield])

	searchfield = so_searchfields + " or " + soi_searchfields

	return frappe.db.sql("""select so.name, so.status, so.transaction_date, soi.item_code,so.customer
			from `tabSales Order` so
		RIGHT JOIN `tabSales Order Item` soi ON (so.name = soi.parent)
		where so.docstatus = 1
			and so.status != "Closed"
			and so.status != "On Hold"
			and soi.item_code = %(item_code)s
			and ({searchfield})
		order by
			if(locate(%(_txt)s, so.name), locate(%(_txt)s, so.name), 99999)
		limit %(start)s, %(page_len)s """.format(searchfield=searchfield), {
			'txt': '%%%s%%' % txt,
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len,
			'item_code': filters.get('production_item'),
		})

def set_required_items(self, reset_only_qty=False):
	'''set required_items for production to keep track of reserved qty'''
	if not reset_only_qty:
		self.required_items = []

	if self.bom_no and self.qty:
		item_dict = get_bom_items_as_dict(self.bom_no, self.company, qty=self.qty,
			fetch_exploded = self.use_multi_level_bom)

		if reset_only_qty:
			for d in self.get("required_items"):
				if item_dict.get(d.item_code):
					d.required_qty = item_dict.get(d.item_code).get("qty")
		else:
			# Attribute a big number (999) to idx for sorting putpose in case idx is NULL
			# For instance in BOM Explosion Item child table, the items coming from sub assembly items

			#Finbyz Changes START: Updated 'merge':item.merge
			for item in sorted(item_dict.values(), key=lambda d: d['idx'] or 9999):
				self.append('required_items', {
					'operation': item.operation,
					'item_code': item.item_code,
					'item_name': item.item_name,
					'merge':item.merge,
					'description': item.description,
					'allow_alternative_item': item.allow_alternative_item,
					'required_qty': item.qty,
					'source_warehouse': item.source_warehouse or item.default_warehouse,
					'include_item_in_manufacturing': item.include_item_in_manufacturing
				})
				# Finbyz Changes END
				if not self.project:
					self.project = item.get("project")

		self.set_available_qty()

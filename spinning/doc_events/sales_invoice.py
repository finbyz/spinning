from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt 

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
    for d in self.taxes:
        if d.account_head in account_list:
            self.gst_taxable_value = flt(d.base_total) - flt(d.base_tax_amount)
            break
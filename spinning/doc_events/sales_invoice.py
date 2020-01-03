from __future__ import unicode_literals
import frappe
from frappe import _

def validate(self,method):
    hsn = self.items[0].gst_hsn_code
    for row in self.items:
        if row.gst_hsn_code != hsn:
            frappe.throw(_("Row: {} HSN code is different".format(row.idx)))
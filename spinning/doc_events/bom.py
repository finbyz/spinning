# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe

@frappe.whitelist()
def before_naming(self, method):
	override_bom_autoname(self)

def override_bom_autoname(self):
	from erpnext.manufacturing.doctype.bom.bom import BOM
	BOM.autoname = bom_autoname

def bom_autoname(self):
	self.name = 'BOM-' + self.merge + "-" + self.item

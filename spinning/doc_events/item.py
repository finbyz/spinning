# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import frappe
from frappe import _

@frappe.whitelist()
def validate(self, method):
	if self.is_new():
		remove_variant_name_from_item_name(self)

def remove_variant_name_from_item_name(self):
	if self.get('variant_of'):
		self.item_name = self.item_name.replace(self.variant_of + "-", "", 1)
		self.description = self.description.replace(self.variant_of, "", 1)

# -*- coding: utf-8 -*-
# Copyright (c) 2019, FinByz Tech Pvt Ltd and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname

class Package(Document):
	
	def autoname(self):
		if self.package_series:
			series = self.package_series + '-.###'
			
			name = None
			while not name:
				name = make_autoname(series, "Package", self)
				if frappe.db.exists('Package', name):
					name = None

			self.package_no = name
			self.name = name
	
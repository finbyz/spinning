# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__version__ = '0.0.1'

import erpnext
from spinning.doc_events.sales_order import create_pick_list
erpnext.selling.doctype.sales_order.sales_order.create_pick_list = create_pick_list

from spinning.override_method import get_itemised_tax_breakup_data, get_item_list

erpnext.regional.india.utils.get_itemised_tax_breakup_data = get_itemised_tax_breakup_data
erpnext.regional.india.utils.get_item_list = get_item_list
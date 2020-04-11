# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__version__ = '0.0.1'

import erpnext
from .doc_events.sales_order import create_pick_list
erpnext.selling.doctype.sales_order.sales_order.create_pick_list = create_pick_list
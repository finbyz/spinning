from __future__ import unicode_literals
from frappe import _

def get_data(data):
	data['fieldname'] = 'pick_list_no'
	data['transactions'] = [
		{
			'label': _('Delivery Note'),
			'items': ['Delivery Note']
		},
	]
	
	return data
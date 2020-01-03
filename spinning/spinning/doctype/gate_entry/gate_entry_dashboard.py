from frappe import _

def get_data():
	return {
		'fieldname': 'gate_entry',
		'transactions': [
			{	
				'label': _('Gate Entry'),
				'items': ['Material Receipt','Purchase Receipt','Material Transfer']
			},	
		]
	}
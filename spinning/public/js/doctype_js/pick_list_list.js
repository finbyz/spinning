frappe.listview_settings['Pick List'] = {
	get_indicator: function(doc) {
		if (doc.docstatus == 1){
			if (doc.user_status_ == 'Close'){
				return [__("Closed"), "blue", "user_status_,=,Close"];
			}
			else if (doc.user_status_ == 'Hold'){
				return [__("Hold"), "blue", "user_status_,=,Hold"];
			}
			else if (doc.status == 'To Deliver'){
				return [__("To Deliver"), "orange", "status,=,To Deliver"];
			}
			else if (doc.status == 'Partially Delivered'){
				return [__("Partially Delivered"), "blue", "status,=,Partially Delivered"];
			}
			else if(doc.status == 'Delivered') {
				return [__("Delivered"), "green", "status,=,Delivered"];
			}
		}
	}
};

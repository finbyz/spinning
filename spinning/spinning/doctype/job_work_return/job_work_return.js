// Copyright (c) 2019, FinByz Tech Pvt Ltd and contributors
// For license information, please see license.txt


frappe.ui.form.on('Job Work Return', {
	refresh: function(frm) {
		frappe.model.with_doc("BOM", frm.doc.bom_no, function() {
			var os_doc = frappe.model.get_doc("BOM", frm.doc.bom_no)
			//console.log("quantity",d.quantity);
			$.each(os_doc.items, function(index, row){
				let d = frm.add_child("items");
				d.item_code = row.item_code;
				//d.qty = flt(flt( os_doc.quantity * row.qty) / frm.doc.qty );
				console.log("quantity",os_doc.quantity * row.qty);

				// d.source_warehouse = frm.doc.default_source_warehouse;
				//d.required_quantity = flt(flt(frm.doc.target_qty * row.quantity) / os_doc.total_qty);
			})
		});

	}
});
this.frm.add_fetch('batch_no', 'merge', 'merge');
this.frm.add_fetch('batch_no', 'grade', 'grade');

this.frm.cscript.onload = function(frm) {
	this.frm.set_query("batch_no", "items", function(doc, cdt, cdn) {
		let d = locals[cdt][cdn];

		if(!d.item_code){
			frappe.throw(__("Please enter Item Code to get batch no."));
		}
		else{
			return {
				query: "spinning.controllers.queries.batch_query",
				filters: {
					'item_code': d.item_code,
					'warehouse': d.warehouse
				}
			}
		}
	});
}

frappe.ui.form.on("Delivery Note Item", {
	item_code: function(frm, cdt, cdn){
		let d = locals[cdt][cdn];
		setTimeout(function(){
			frappe.db.get_value("Batch", d.batch_no, ['merge', 'grade'], function(r){
				frappe.model.set_value(cdt, cdn, 'merge', r.merge);
				frappe.model.set_value(cdt, cdn, 'grade', r.grade);
			})
		}, 1000);
	},
});

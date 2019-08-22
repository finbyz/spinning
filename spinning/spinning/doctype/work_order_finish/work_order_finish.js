// Copyright (c) 2019, FinByz Tech Pvt Ltd and contributors
// For license information, please see license.txt

cur_frm.fields_dict.grade.get_query = function(doc) {
	return {
		filters: {
			"supplier": doc.company
		}
	}
};

frappe.ui.form.on("Work Order Finish", {
	before_save: function(frm){
		frm.trigger("cal_total");
	},
	cal_total: function(frm){
		let spool = 0;
		let net_weight = 0.0;
		let gross_weight = 0.0;
		let tare_weight = 0.0;
		let total_tare_weight = 0.0 ;
		
		frm.doc.package_details.forEach(function (d) {
			spool += d.no_of_spool;
			gross_weight += d.gross_weight;
			tare_weight = flt(d.package_weight+(d.no_of_spool*frm.doc.spool_weight))
			total_tare_weight += d.tare_weight;
			frappe.model.set_value(d.doctype,d.name,"tare_weight",tare_weight);
			frappe.model.set_value(d.doctype,d.name,"net_weight",flt(d.gross_weight - d.tare_weight))
			net_weight += d.net_weight;
		});
		frm.set_value("total_spool",spool);
		frm.set_value("total_net_weight",net_weight);
		frm.set_value("total_gross_weight",gross_weight);
		frm.set_value("total_tare_weight",total_tare_weight);
	},
});

frappe.ui.form.on("Work Order Finish Detail", {
	 gross_weight: function (frm, cdt, cdn) {
		let d = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "net_weight", flt(d.gross_weight - d.tare_weight));
	 },

	 package_weight: function (frm, cdt, cdn) {
		let d = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "tare_weight", flt(d.package_weight + (d.no_of_spool * frm.doc.spool_weight)));
		frappe.model.set_value(cdt, cdn, "net_weight", flt(d.gross_weight - d.tare_weight));
	 },
	 
	 no_of_spool: function (frm, cdt, cdn) {
		let d = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "tare_weight", flt(d.package_weight + (d.no_of_spool * frm.doc.spool_weight)));
		frappe.model.set_value(cdt, cdn, "net_weight", flt(d.gross_weight - d.tare_weight));
	 },
	 
	 print: function(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		frm.call({
			doc: frm.doc,
			method: 'print_row_package',
			args: {
				child_row: row
			},
			callback: function(r) {
				frm.reload_doc();
			}
		});
	 }
});
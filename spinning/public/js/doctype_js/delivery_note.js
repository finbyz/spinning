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

cur_frm.fields_dict.packages.grid.get_field('package').get_query = function(doc) {
	let items = [...new Set((frm.doc.items || []).map(function(i){return i.item_code}))]
	return {
		filters: {
			"status": ["!=", "Out of Stock"],
			"item_code": ['in', items]
		}
	}
}

cur_frm.fields_dict.taxes_and_charges.get_query = function(doc){
	return {
		"filters": {
			'company': doc.company
		}
	};
}

frappe.ui.form.on("Delivery Note", {
	add_packages: function(frm){
		select_packages({frm: frm, merge: frm.doc.merge});
	}
});

frappe.ui.form.on("Delivery Note Item", {
	item_code: function(frm, cdt, cdn){
		let d = locals[cdt][cdn];
		setTimeout(function(){
			frappe.db.get_value("Batch", d.batch_no, ['merge', 'grade'], function(r){
				frappe.model.set_value(cdt, cdn, 'merge', r.merge);
				frappe.model.set_value(cdt, cdn, 'grade', r.grade);
				
				select_packages({frm: frm, item_code: d.item_code, merge: d.merge, warehouse: d.warehouse});
			});

		}, 1000);
	},
});

const select_packages = (args) => {
	frappe.require("assets/spinning/js/utils/package_selector.js", function() {
		new PackageSelector(args)
	})
}
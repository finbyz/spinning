// Copyright (c) 2019, FinByz Tech Pvt Ltd and contributors
// For license information, please see license.txt

cur_frm.fields_dict.t_warehouse.get_query = function (doc) {
    return {
        filters: {
            "company": doc.company
        }
    }
};
cur_frm.fields_dict.s_warehouse.get_query = function (doc) {
    return {
        filters: {
            "company": doc.company
        }
    }
};
cur_frm.fields_dict.merge.get_query = function (doc) {
    return {
        filters: {
            "item_code": doc.item_code
        }
    }
};
cur_frm.fields_dict.grade.get_query = function(doc) {
	return{
		query: "spinning.controllers.queries.grade_query",
		filters: {
			'item_code': doc.item_code
		}
	}
};
cur_frm.fields_dict.bom_no.get_query = function (doc) {
    return {
        filters: {
			"item": doc.item_code,
			"docstatus": 1
        }
    }
};


// cur_frm.fields_dict.items.grid.get_field("merge").get_query = function (doc, cdt, cdn) {
//     var d = locals[cdt][cdn];
//     return {
//     	filters: {
//         	"item_code": d.item_code
//     	}
//     }
// };


cur_frm.fields_dict.default_package_item.get_query = function (doc) {
    return {
        filters: {
            "item_group": doc.default_package_type
        }
    }
};


frappe.ui.form.on('Job Work Return', {
	refresh(frm) {
		// your code here
	},
	bom_no: function(frm){
		frm.set_value("qty", "");
		frm.doc.items = [];
		refresh_field('items');
	},
	qty: function(frm){
		frm.doc.items = [];
		refresh_field('items');
		if (frm.doc.qty !== ""){
			frappe.model.with_doc("BOM", frm.doc.bom_no, function() {
				var os_doc = frappe.model.get_doc("BOM", frm.doc.bom_no);

				$.each(os_doc.items, function(index, row){
					let d = frm.add_child("items");

					d.item_code = row.item_code;
					d.item_name = row.item_name;
					d.uom = row.uom;
					d.basic_rate = row.rate;
					d.merge = row.merge;
					//console.log("quantity",os_doc.quantity);
					d.qty = flt(flt(frm.doc.qty * row.qty) / os_doc.quantity);
					d.amount = d.basic_rate * d.qty;
				});
				frm.refresh_field('items');
			});
		}
	},
	before_save: function(frm){
		frm.trigger('cal_total_package_gross_wt');
		frm.trigger('cal_total_package_net_wt');
	},
	cal_total_package_gross_wt: function(frm){
		const total_gross_wt = frappe.utils.sum((frm.doc.package_details || []).map(function(i){ return i.gross_weight }));
		frm.set_value("total_gross_weight", flt(total_gross_wt));
	},

	cal_total_package_net_wt: function(frm){
		const total_net_wt = frappe.utils.sum((frm.doc.package_details || []).map(function(i){ return i.net_weight }));
		frm.set_value("total_net_weight", flt(total_net_wt));
	},
	set_pkg_type_item : function (frm) {
		$.each(frm.doc.package_details || [], function(i, d) {
			d.package_item = frm.doc.default_package_item;
			d.package_type = frm.doc.default_package_type;
		});
		refresh_field("package_details");
	},
	default_package_item: function(frm) {
		frm.trigger('set_pkg_type_item');
	},
	default_package_type: function(frm) {
		frm.trigger('set_pkg_type_item');
	},
	is_returnable: function(frm) {
		$.each(frm.doc.package_details || [], function(i, d) {
			d.is_returnable = frm.doc.is_returnable;
		});
		refresh_field("package_details");
	},
	returnable_by: function(frm) {
		$.each(frm.doc.package_details || [], function(i, d) {
			d.returnable_by = frm.doc.returnable_by;
		});
		refresh_field("package_details");
	},
});

frappe.ui.form.on("Job Work Return Package Details", {
	items_add: function(frm, cdt, cdn){
		console.log("hello");
	},
	gross_weight: function(frm, cdt, cdn){
		frm.events.cal_total_package_gross_wt(frm)
	},
	net_weight: function(frm, cdt, cdn){
		frm.events.cal_total_package_net_wt(frm)
	},

	packages_remove: function(frm, cdt, cdn){
		frm.events.cal_total_package_net_wt(frm)
	},
	packages_add: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		row.package_item = frm.doc.package_item;
		row.package_type = frm.doc.default_package_type;
		row.is_returnable = frm.doc.is_returnable;
		row.returnable_by = frm.doc.returnable_by;
		frm.refresh_field("package_details");
	},
});
frappe.ui.form.on("Job Work Return Item", {
	items_add: function(frm, cdt, cdn){
		console.log("hello");
	
	},
	qty: function(frm, cdt, cdn){
		var d = locals[cdt][cdn]
		frappe.model.set_value(d.doctype, d.name, 'amount', flt(d.qty * d.basic_rate));
		frappe.model.set_value(d.doctype, d.name, 'basic_amount', flt(d.amount));
	},

	basic_rate: function(frm, cdt, cdn){
		var d = locals[cdt][cdn]
		frappe.model.set_value(d.doctype, d.name, 'amount', flt(d.qty * d.basic_rate));
		frappe.model.set_value(d.doctype, d.name, 'basic_amount', flt(d.amount));
	},
});
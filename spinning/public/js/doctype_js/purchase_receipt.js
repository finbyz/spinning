cur_frm.fields_dict['items'].grid.get_field("merge").get_query = function(doc, cdt, cdn) {
	let d = locals[cdt][cdn];

	return {
		filters: {
			"item_code": d.item_code
		}
	}
};

this.frm.fields_dict.taxes_and_charges.get_query = function(doc){
	return {
		"filters": {
			'company': doc.company
		}
	};
}

/* cur_frm.fields_dict['items'].grid.get_field("grade").get_query = function(doc) {
	return {
		filters: {
			"supplier": doc.supplier
		}
	}
}; */
cur_frm.fields_dict.package_item.get_query = function (doc) {
    return {
        filters: {
            "item_group": doc.package_type
        }
    }
};
frappe.ui.form.on('Purchase Receipt', {
	onload: function(frm){
		frm.trigger('override_merge_new_doc');
		frm.trigger('override_grade_new_doc');
		frm.trigger('set_options_for_row_ref');
	},
	
	override_merge_new_doc: function(frm){
		let merge_field = cur_frm.get_docfield("items", "merge")

		merge_field.get_route_options_for_new_doc = function(row){
			return {
				'item_code': row.doc.item_code
			}
		}
	},
	
	override_grade_new_doc: function(frm){
		let grade_field = cur_frm.get_docfield("items", "grade")

		grade_field.get_route_options_for_new_doc = function(row){
			return {
				'supplier': frm.doc.supplier
			}
		}
	},

	set_options_for_row_ref: function(frm){
		let options = [];
		let row_ref_doc_field = frm.get_docfield("packages", "row_ref");
		const items_length = frm.doc.items.length;

		for(let i = 1; i <= items_length; i++){
			options.push(i.toString())
		}
		row_ref_doc_field.options = options.join("\n");
	},
	
	cal_total_package_gross_wt: function(frm){
		const total_gross_wt = frappe.utils.sum((frm.doc.packages || []).map(function(i){ return i.gross_weight }));
		frm.set_value("total_package_gross_weight", flt(total_gross_wt));
	},

	cal_total_package_net_wt: function(frm){
		const total_net_wt = frappe.utils.sum((frm.doc.packages || []).map(function(i){ return i.net_weight }));
		frm.set_value("total_package_net_weight", flt(total_net_wt));
	},
	add_packages: function(frm){
		select_packages({frm: frm, merge: frm.doc.merge});
	}
});

frappe.ui.form.on('Purchase Receipt Item', {
	items_add: function(frm, cdt, cdn){
		frm.events.set_options_for_row_ref(frm);
	},

	items_remove: function(frm, cdt, cdn){
		frm.events.set_options_for_row_ref(frm);
	},
	item_code: function(frm, cdt, cdn){
		let d = locals[cdt][cdn];
		if(d.has_batch_no){
			select_packages({frm: frm, item_code: d.item_code, merge: d.merge});
		}
	}
});

frappe.ui.form.on("Purchase Receipt Package Detail", {
	gross_weight: function(frm, cdt, cdn){
		frm.events.cal_total_package_gross_wt(frm)
	},

	net_weight: function(frm, cdt, cdn){
		frm.events.cal_total_package_net_wt(frm)
	},

	packages_remove: function(frm, cdt, cdn){
		frm.events.cal_total_package_net_wt(frm)
	}
});
const select_packages = (args) => {
	frappe.require("assets/spinning/js/utils/package_selector.js", function() {
		new PackageSelector(args)
	})
}
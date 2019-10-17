// Copyright (c) 2019, FinByz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* 
cur_frm.fields_dict.grade.get_query = function(doc) {
	return {
		filters: {
			"supplier": doc.company
		}
	}
}; */
cur_frm.fields_dict.package_item.get_query = function(doc) {
	return {
		filters: {
			"item_group": doc.package_type
		}
	}
};
cur_frm.fields_dict.package_warehouse.get_query = function (doc) {
    return {
        filters: {
            "company": doc.company
        }
    }
};
cur_frm.fields_dict.source_warehouse.get_query = function (doc) {
    return {
        filters: {
            "company": doc.company
        }
    }
};
cur_frm.fields_dict.target_warehouse.get_query = function (doc) {
    return {
        filters: {
            "company": doc.company
        }
    }
};

frappe.ui.form.on("Work Order Finish", {
	onload: function(frm){
		if(frm.doc.__islocal){
			frappe.db.get_value("Company", frm.doc.company, 'abbr', function(r){
				frm.set_value('package_warehouse','Carton Warehouse - ' + r.abbr)
			});
		}
		frm.events.set_package_series(frm);
	},

	before_save: function(frm){
		//frm.trigger("cal_total");
	},

	set_package_series: function(frm){
		return frappe.call({
			doc: frm.doc,
			method: "set_package_series",
			callback: function(r){
				frm.refresh_field('package_series');
				frm.refresh_field('series_value');
				cur_frm.set_df_property('series_value', 'description', r.message);
			}
		})
	},

	update_series_number: function(frm){
		return frappe.call({
			doc: frm.doc,
			method: "update_series_number",
			callback: function(r){
				cur_frm.reload_doc();
			}
		})
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
		if(frm.doc.__islocal){
			frappe.throw(__("Please save the document first."));
			return false;
		}

		var row = locals[cdt][cdn];
		frm.call({
			doc: frm.doc,
			method: 'print_row_package',
			args: {
				child_row: row
			},
			callback: function(r) {
				frm.reload_doc();
				var w = window.open(frappe.urllib.get_full_url("/printview?"
						+ "doctype=" + encodeURIComponent("Work Order Finish Detail")
						+ "&name=" + encodeURIComponent(r.message)
						+ ("&trigger_print=1")
						+ "&format=" + encodeURIComponent("Single Packing Sticker")
						//+ "&no_letterhead=" + (cur_frm.with_letterhead() ? "0" : "1")
						//+ (cur_frm.lang_code ? ("&_lang=" + cur_frm.lang_code) : "")
						));
					if (!w) {
						frappe.msgprint(__("Please enable pop-ups")); return;
					}
				//cur_frm.print_doc();
			}
		});
	},	
});
cur_frm.fields_dict['locations'].grid.get_field("merge").get_query = function(doc, cdt, cdn) {
	let d = locals[cdt][cdn];

	return {
		filters: {
			"item_code": d.item_code
		}
	}
};
cur_frm.fields_dict['locations'].grid.get_field("grade").get_query = function(doc, cdt, cdn) {
	let d = locals[cdt][cdn];

	return {
		query: 'spinning.controllers.queries.grade_query',
		filters: {
			"item_code": d.item_code,
		}
	}
};

frappe.ui.form.on('Pick List', {
	setup: (frm) => {
		frm.clear_custom_buttons()
	},
	refresh: (frm) => {
		frm.clear_custom_buttons()
		if (frm.doc.docstatus == 1) {
			if (frm.doc.purpose === 'Delivery against Sales Order') {
				frm.add_custom_button(__('Delivery Note'), () => frm.trigger('create_delivery_note2'), __('Create'));
			} else {
				frm.add_custom_button(__('Stock Entry'), () => frm.trigger('create_stock_entry'), __('Create'));
			}
			if (frm.doc.docstatus == 1){
				if (frm.doc.user_status_ == "Open"){
					frm.add_custom_button(__('Close'), () => frm.trigger('close_pl'), __('Status'));
					frm.add_custom_button(__('Hold'), () => frm.trigger('hold_pl'), __('Status'));					
				}
				else{
					frm.add_custom_button(__('Open'), () => frm.trigger('open_pl'), __('Status'));
				}
			}
		}
		frm.set_df_property("company", "read_only", (!frm.doc.__islocal || frm.doc.amended_from) ? 1 : 0);
	},
	close_pl: function(frm){
		frappe.call({
			method: "spinning.doc_events.pick_list.update_status",
			args: {
				'name': frm.doc.name,
				'update_status_': 'Close'
			},
			callback: function(r){
				if (r.message){
					frm.reload_doc()
				}
			}
		})
	},
	hold_pl: function(frm){
		frappe.call({
			method: "spinning.doc_events.pick_list.update_status",
			args: {
				'name': frm.doc.name,
				'update_status_': 'Hold'
			},
			callback: function(r){
				if (r.message){
					frm.reload_doc()
				}
			}
		})
	},
	open_pl: function(frm) {
		frappe.call({
			method: "spinning.doc_events.pick_list.update_status",
			args: {
				'name': frm.doc.name,
				'update_status_': 'Open'
			},
			callback: function(r){
				if (r.message){
					frm.reload_doc()
				}
			}
		})
	},
	update_items: function (frm) {
		select_items({
			frm: frm
		});
	},
	create_delivery_note2: (frm) => {
		frappe.model.open_mapped_doc({
			method: 'spinning.doc_events.pick_list.create_delivery_note',
			frm: frm
		});
	},
});

frappe.ui.form.on('Pick List Item', {
	'unpick_item': (frm, cdt, cdn) => {
		let d = locals[cdt][cdn]

		frappe.call({
			method: "spinning.doc_events.pick_list.unpick_item",
			args: {
				'name': d.name
			},
			callback: function(r){
				if (r.message == "success"){
					location.reload();
				}
			}
		})
	},
	grade: function (frm, cdt, cdn) {
		let d = locals[cdt][cdn];
		if(d.merge){
			frappe.call({
				method: "spinning.controllers.batch_controller.get_batch_no",
				args: {
					'args': {
						'item_code': d.item_code,
						'merge': d.merge,
						'grade': d.grade
					},
				},
				callback: function(r) {
					if(r.message){
						frappe.model.set_value(cdt, cdn, 'batch_no', r.message);
						frm.refresh_field('locations');
					}
					else {
						frappe.model.set_value(cdt, cdn, 'batch_no', null);
					}
				 }
			});
		}
		
    },
	merge: function (frm, cdt, cdn) {
		let d = locals[cdt][cdn];
		if(d.grade){
			frappe.call({
				method: "spinning.controllers.batch_controller.get_batch_no",
				args: {
					'args': {
						'item_code': d.item_code,
						'merge': d.merge,
						'grade': d.grade
					},
				},
				callback: function(r) {
					if(r.message){
						frappe.model.set_value(cdt, cdn, 'batch_no', r.message);
						frm.refresh_field('locations');
					}
					else {
						frappe.model.set_value(cdt, cdn, 'batch_no', null);
					}
				 }			 
			});
		}
		
	},
	batch_no: function(frm, cdt, cdn){
		get_available_qty(frm, cdt, cdn)
	},
	warehouse: function(frm) {
		get_available_qty(frm, cdt, cdn)
	}
})

const select_items = (args) => {
	frappe.require("assets/spinning/js/utils/item_selector.js", function () {
		new ItemSelector(args)
	})
}

function get_available_qty(frm, cdt, cdn) {
	let d = locals[cdt][cdn]
	if (d.batch_no && d.warehouse){
		frappe.db.get_value("Stock Ledger Entry", {'company': frm.doc.company,'item_code': d.item_code, 'batch_no': d.batch_no, 'warehouse': d.warehouse}, "sum(actual_qty) as available_qty").then(function(r){
			frappe.model.set_value(cdt, cdn, 'available_qty', r.message.available_qty || '0')
		})
	}
	else if (d.batch_no){
		frappe.db.get_value("Stock Ledger Entry", {'company': frm.doc.company,'item_code': d.item_code, 'batch_no': d.batch_no}, "sum(actual_qty) as available_qty").then(function(r){
			frappe.model.set_value(cdt, cdn, 'available_qty', r.message.available_qty || '0')
		})
	} else {
		frappe.model.set_value(cdt, cdn, 'available_qty', '0')
	}
	frm.refresh_field('locations')
}
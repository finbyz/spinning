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
		}
		frm.set_df_property("company", "read_only", (!frm.doc.__islocal || frm.doc.amended_from) ? 1 : 0);
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
	}
})

const select_items = (args) => {
	frappe.require("assets/spinning/js/utils/item_selector.js", function () {
		new ItemSelector(args)
	})
}
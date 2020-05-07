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

const select_items = (args) => {
	frappe.require("assets/spinning/js/utils/item_selector.js", function () {
		new ItemSelector(args)
	})
}
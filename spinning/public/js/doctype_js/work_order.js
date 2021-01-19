frappe.ui.form.on("Work Order", {
    setup: function(frm) {
        frm.remove_custom_button('Re-open', 'Status');
        cur_frm.set_query('sales_order', function(doc) {
                return {
                    query: "spinning.doc_events.work_order.sales_order_query",
                    filters: {
                        "production_item": doc.production_item,
                    }
               }
        })
    },
    refresh: function(frm){
        frm.remove_custom_button('Re-open', 'Status');
    }
})
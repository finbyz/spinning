this.frm.cscript.onload = function (frm) {
    // this.frm.fields_dict.items.grid.get_field("ref_no").get_query = function (doc) {
    //     return {
    //         filters: {
    //             "product_name": doc.items.item_code,
    //         }
    //     }
    // };
}
frappe.ui.form.on("Sales Order", {
    onload: function (frm) {
        if (frm.doc.__islocal){
            frm.set_value("tc_name", "SO Specification");
            frm.trigger("set_default_bank_account");
        }
        
        cur_frm.cscript.onload = function(frm) {
            cur_frm.set_query('shipping_address_name', function(doc) {
                return {
                    query: 'frappe.contacts.doctype.address.address.address_query',
                    filters: {
                        link_doctype: 'Customer',
                        link_name: doc.customer
                    }
                };
            }),
            cur_frm.set_query("customer_address", function (doc) {
                return {
                    query: "frappe.contacts.doctype.address.address.address_query",
                    filters: { link_doctype: "Customer", link_name: doc.customer }
                };
            }),
            cur_frm.set_query("contact_person", function (doc) {
                return {
                    query: "frappe.contacts.doctype.contact.contact.contact_query",
                    filters: { link_doctype: "Customer", link_name: doc.customer }
                };
            });
        }
    },
    company: function (frm) {
        frm.trigger("set_default_bank_account");
    },
    set_default_bank_account: function (frm) {
        frappe.db.get_value("Bank Account", { 'is_default': 1,'is_company_account':1, 'company': frm.doc.company }, 'name', function(r) {
            if (r.name) {
                frm.set_value('bank_account',r.name)
            }
        })
    },
    before_save: function (frm) {
        frm.trigger("cal_total");
        frm.trigger("box_cal");
        /*frm.doc.items.forEach(function (d) {
            frappe.call({
                method: 'exim.api.get_customer_ref_code',
                args: {
                    'item_code': d.item_code,
                    'customer': frm.doc.customer,
                },
                callback: function (r) {
                    if (r.message) {
                        frappe.model.set_value(d.doctype, d.name, 'item_name', r.message);
                    }
                }
            })
        });*/
        frm.refresh_field('items');
    },
    refresh: function (frm) {
        if (!in_list(["Closed", "Completed"], frm.doc.status)) {
            if (frm.doc.docstatus == 1) {
                frm.add_custom_button(__("LC"), function () {
                    frappe.model.open_mapped_doc({
                        method: "exim.api.make_lc",
                        frm: cur_frm
                    })
                }, __("Create"))
            }

        }
        frm.set_df_property("company", "read_only", (!frm.doc.__islocal || frm.doc.amended_from) ? 1 : 0);
    },
    cal_total: function (frm) {
        let total_qty = 0.0;
        let total_gr_wt = 0.0;
        let total_packages = 0.0;

        frm.doc.items.forEach(function (d) {
            total_qty += flt(d.qty);
            total_gr_wt += flt(d.gross_wt);
            total_packages += flt(d.no_of_packages);
        });

        frm.set_value("total_qty", total_qty);
        frm.set_value("total_gr_wt", total_gr_wt);
        frm.set_value("total_packages", total_packages);
    },
    box_cal: function (frm) {
        frm.doc.items.forEach(function (d, i) {
            if (i == 0) {
                d.packages_from = 1;
                d.packages_to = d.no_of_packages;
            }
            else {
                d.packages_from = Math.round(frm.doc.items[i - 1].packages_to + 1);
                d.packages_to = Math.round(d.packages_from + d.no_of_packages - 1);
            }
        });
        frm.refresh_field('items');
    },
    pallet_cal: function (frm) {
        frm.doc.items.forEach(function (d, i) {
            if (d.palleted) {
                if (i == 0) {
                    d.pallet_no_from = 1;
                    d.pallet_no_to = Math.round(d.total_pallets);
                }
                else {
                    d.pallet_no_from = Math.round(frm.doc.items[i - 1].pallet_no_to + 1);
                    d.pallet_no_to = Math.round(d.pallet_no_from + d.total_pallets - 1);
                }
            }
        });
        frm.refresh_field('items');
    },
    update_items: (frm) => {

    }

});
frappe.ui.form.on("Sales Order Item", {
    pallet_size: function (frm, cdt, cdn) {
        frappe.run_serially([
            () => {
                let d = locals[cdt][cdn];
                frappe.model.set_value(cdt, cdn, "total_pallets", Math.round(d.qty / d.pallet_size));
            },
            () => {
                frm.events.pallet_cal(frm);
            }
        ]);
    },
    no_of_packages: function (frm, cdt, cdn) {
        frm.events.box_cal(frm);
        frm.events.cal_total(frm);
    },

});

erpnext.selling.SalesOrderController = erpnext.selling.SalesOrderController.extend({
    refresh: function (doc, dt, dn) {
        var me = this;
        // this._super();
        let allow_delivery = false;

        if (doc.docstatus == 1) {
            if (this.frm.has_perm("submit")) {
                if (doc.status === 'On Hold') {
                    // un-hold
                    this.frm.add_custom_button(__('Resume'), function () {
                        me.frm.cscript.update_status('Resume', 'Draft')
                    }, __("Status"));

                    if (flt(doc.per_delivered, 6) < 100 || flt(doc.per_billed) < 100) {
                        // close
                        this.frm.add_custom_button(__('Close'), () => this.close_sales_order(), __("Status"))
                    }
                }
                else if (doc.status === 'Closed') {
                    // un-close
                    this.frm.add_custom_button(__('Re-open'), function () {
                        me.frm.cscript.update_status('Re-open', 'Draft')
                    }, __("Status"));
                }
            }
            if (doc.status !== 'Closed') {
                if (doc.status !== 'On Hold') {

                    allow_delivery = this.frm.doc.items.some(item => item.delivered_by_supplier === 0 && item.qty > flt(item.delivered_qty))

                    if (this.frm.has_perm("submit")) {
                        if (flt(doc.per_delivered, 6) < 100 || flt(doc.per_billed) < 100) {
                            // hold
                            this.frm.add_custom_button(__('Hold'), () => this.hold_sales_order(), __("Status"))
                            // close
                            this.frm.add_custom_button(__('Close'), () => this.close_sales_order(), __("Status"))
                        }
                    }

                    // delivery note
                    if (flt(doc.per_delivered, 6) < 100 && ["Sales", "Shopping Cart"].indexOf(doc.order_type) !== -1 && allow_delivery) {
                        this.frm.add_custom_button(__('Pick List'), () => this.create_pick_list(), __('Create'));
                        this.frm.add_custom_button(__('Delivery'), () => this.make_delivery_note_based_on_delivery_date(), __('Create'));
                        this.frm.add_custom_button(__('Work Order'), () => this.make_work_order(), __('Create'));
                    }

                    // sales invoice
                    // if (flt(doc.per_billed, 6) < 100) {
                    //     this.frm.add_custom_button(__('Invoice'), () => me.make_sales_invoice(), __('Create'));
                    // }

                    // material request
                    if (!doc.order_type || ["Sales", "Shopping Cart"].indexOf(doc.order_type) !== -1
                        && flt(doc.per_delivered, 6) < 100) {
                        this.frm.add_custom_button(__('Material Request'), () => this.make_material_request(), __('Create'));
                        this.frm.add_custom_button(__('Request for Raw Materials'), () => this.make_raw_material_request(), __('Create'));
                    }

                    // make purchase order
                    this.frm.add_custom_button(__('Purchase Order'), () => this.make_purchase_order(), __('Create'));

                    // maintenance
                    if (flt(doc.per_delivered, 2) < 100 &&
                        ["Sales", "Shopping Cart"].indexOf(doc.order_type) === -1) {
                        this.frm.add_custom_button(__('Maintenance Visit'), () => this.make_maintenance_visit(), __('Create'));
                        this.frm.add_custom_button(__('Maintenance Schedule'), () => this.make_maintenance_schedule(), __('Create'));
                    }

                    // project
                    // if (flt(doc.per_delivered, 2) < 100 && ["Sales", "Shopping Cart"].indexOf(doc.order_type) !== -1 && allow_delivery) {
                    //     this.frm.add_custom_button(__('Project'), () => this.make_project(), __('Create'));
                    // }

                    // if (!doc.auto_repeat) {
                    //     this.frm.add_custom_button(__('Subscription'), function () {
                    //         erpnext.utils.make_subscription(doc.doctype, doc.name)
                    //     }, __('Create'))
                    // }

                    if (doc.docstatus === 1 && !doc.inter_company_order_reference) {
                        let me = this;
                        frappe.model.with_doc("Customer", me.frm.doc.customer, () => {
                            let customer = frappe.model.get_doc("Customer", me.frm.doc.customer);
                            let internal = customer.is_internal_customer;
                            let disabled = customer.disabled;
                            if (internal === 1 && disabled === 0) {
                                me.frm.add_custom_button("Inter Company Order", function () {
                                    me.make_inter_company_order();
                                }, __('Create'));
                            }
                        });
                    }
                }
                // payment request
                // if (flt(doc.per_billed) == 0) {
                //     this.frm.add_custom_button(__('Payment Request'), () => this.make_payment_request(), __('Create'));
                //     this.frm.add_custom_button(__('Payment'), () => this.make_payment_entry(), __('Create'));
                // }
                this.frm.page.set_inner_btn_group_as_primary(__('Create'));
            }
        }

        if (this.frm.doc.docstatus === 0) {
            this.frm.add_custom_button(__('Quotation'),
                function () {
                    erpnext.utils.map_current_doc({
                        method: "erpnext.selling.doctype.quotation.quotation.make_sales_order",
                        source_doctype: "Quotation",
                        target: me.frm,
                        setters: [
                            {
                                label: "Customer",
                                fieldname: "party_name",
                                fieldtype: "Link",
                                options: "Customer",
                                default: me.frm.doc.customer || undefined
                            }
                        ],
                        get_query_filters: {
                            company: me.frm.doc.company,
                            docstatus: 1,
                            status: ["!=", "Lost"]
                        }
                    })
                }, __("Get items from"));
        }

        this.order_type(doc);
    },
    make_delivery_note_based_on_delivery_date: function() {
		var me = this;

		var delivery_dates = [];
		$.each(this.frm.doc.items || [], function(i, d) {
			if(!delivery_dates.includes(d.delivery_date)) {
				delivery_dates.push(d.delivery_date);
			}
		});

		var item_grid = this.frm.fields_dict["items"].grid;
		if(!item_grid.get_selected().length && delivery_dates.length > 1) {
			var dialog = new frappe.ui.Dialog({
				title: __("Select Items based on Delivery Date"),
				fields: [{fieldtype: "HTML", fieldname: "dates_html"}]
			});

			var html = $(`
				<div style="border: 1px solid #d1d8dd">
					<div class="list-item list-item--head">
						<div class="list-item__content list-item__content--flex-2">
							${__('Delivery Date')}
						</div>
					</div>
					${delivery_dates.map(date => `
						<div class="list-item">
							<div class="list-item__content list-item__content--flex-2">
								<label>
								<input type="checkbox" data-date="${date}" checked="checked"/>
								${frappe.datetime.str_to_user(date)}
								</label>
							</div>
						</div>
					`).join("")}
				</div>
			`);

			var wrapper = dialog.fields_dict.dates_html.$wrapper;
			wrapper.html(html);

			dialog.set_primary_action(__("Select"), function() {
				var dates = wrapper.find('input[type=checkbox]:checked')
					.map((i, el) => $(el).attr('data-date')).toArray();

				if(!dates) return;

				$.each(dates, function(i, d) {
					$.each(item_grid.grid_rows || [], function(j, row) {
						if(row.doc.delivery_date == d) {
							row.doc.__checked = 1;
						}
					});
				})
				me.make_delivery_note();
				dialog.hide();
			});
			dialog.show();
		} else {
			this.make_delivery_note();
		}
	},

    make_delivery_note: function() {
        console.log('test')
		frappe.model.open_mapped_doc({
			// method: "erpnext.selling.doctype.sales_order.sales_order.make_delivery_note",
			method: "spinning.doc_events.sales_order.make_delivery_note",
			frm: me.frm
		})
	},
});
$.extend(cur_frm.cscript, new erpnext.selling.SalesOrderController({ frm: cur_frm }));

var select_packages = (args) => {
	frappe.require("assets/spinning/js/utils/item_selector.js", function() {
		new ItemSelector(args)
	})
}
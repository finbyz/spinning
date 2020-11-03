// Copyright (c) 2019, FinByz Tech Pvt Ltd and contributors
// For license information, please see license.txt


frappe.ui.form.on('Gate Exit', {
	onload: function (frm) {
		if (frm.doc.document_type != 'Delivery Note') {
			frm.fields_dict.document_number.get_query = function (doc) {
				return {
					filters: {
						"send_to_party": 1
					}
				};
			}
		}
		if (frm.doc.__islocal){
			
			frm.trigger('naming_series');
		}
		
	},
	naming_series: function (frm) {
		if (frappe.meta.get_docfield("Gate Exit", "series_value", frm.doc.name)){
			if (frm.doc.__islocal && frm.doc.company && !frm.doc.amended_from) {
				
				frappe.call({
					method: "finbyzerp.api.check_counter_series",
					args: {
						'name': frm.doc.naming_series,
						'date': frm.doc.posting_date,
						'company_series': frm.doc.company_series || null,
					},
					callback: function (e) {
						// frm.doc.series_value = e.message;
						frm.set_value('series_value', e.message);
					}
				});
				// frm.refresh_field('series_value')
			}
		}
	},
	company: function (frm) {
		frm.trigger('naming_series');
	},
	posting_date: function (frm) {
		frm.trigger('naming_series');
	},
	calculate_package_qty : function(frm) {
		let items = frm.doc.items;
		let total = {"total_qty" : 0,'total_packages': 0};

		$.each(items, (i,v) => {
			 total['total_qty'] += items[i]["qty"];
			 total['total_packages'] += items[i]["no_of_packages"];
		})
		frm.set_value('total_packages', total['total_packages']);
		frm.set_value('total_qty', total['total_qty']);
	},
	refresh : function(frm) {
		// your code here
		frm.trigger('calculate_package_qty');
	},
	validate: function(frm) {
		// console.log("hello");
		frm.trigger('calculate_package_qty');

	},
	party: function(frm) {
		frappe.call({
			method:"erpnext.accounts.party.get_party_details",
			args:{
				party: frm.doc.party,
				party_type: frm.doc.party_type
			},
			callback: function(r){
				if(r.message){
					frm.set_value ('party_name', frm.doc.party);
					frm.set_value('address_display', r.message.address_display);
					// if(frm.doc.document_type != 'Delivery Note' && frm.doc.document_number){
					// 	frm.set_value('shipping_address', r.message.shipping_address);
					// }
				}
			}
		})
	},
	document_number: function (frm) {
		frm.trigger('get_address');
	    frm.doc.items = [];
	    refresh_field('items');
	    if (frm.doc.document_number){
	    
	        frappe.model.with_doc(frm.doc.document_type, frm.doc.document_number, function(){
	        var item_doc = frappe.model.get_doc(frm.doc.document_type, frm.doc.document_number);
	        
	        $.each(item_doc.items, function(index, row){
	            let d = frm.add_child("items");
	           // d.item_code = row.item_name;
	           //d.name = row.item_name;
	           d.item_code = row.item_code;
	           d.item_name = row.item_name;
	           d.qty = row.qty;
	           d.merge = row.merge;
	           d.grade = row.grade;
	           d.no_of_packages = row.no_of_packages;
	           // d.item_code = row.item.code;
	        });
			frm.refresh_field('items');
			//frm.set_value('shipping_address',item_doc.shipping_address)
			frm.trigger('calculate_package_qty');
		
	    });
	    }
	},
	document_type: function(frm){
		frm.set_value('document_number', '');
		frm.set_value('party_type', '');
		frm.set_value('party', '');
		frm.set_value('party_name', '');
	},
	get_address: function (frm) { 
		if(frm.doc.document_type == 'Delivery Note' && frm.doc.document_number){
			frm.set_value('party_type', 'Customer');
			frappe.db.get_value(frm.doc.document_type, frm.doc.document_number, 'customer', function (d) {		
				frm.set_value('party',d.customer)
			})
			frappe.db.get_value(frm.doc.document_type, frm.doc.document_number, 'shipping_address', function (d) {	
				frm.set_value('shipping_address',d.shipping_address)
			})
		}
		else if(frm.doc.document_type == 'Purchase Receipt' && frm.doc.document_number){
			frm.set_value('party_type', 'Supplier');
			frappe.db.get_value(frm.doc.document_type, frm.doc.document_number, 'supplier', function (d) {		
				frm.set_value('party',d.supplier)
			})
			frappe.db.get_value(frm.doc.document_type, frm.doc.document_number, 'shipping_address_display', function (d) {	
				frm.set_value('shipping_address',d.shipping_address_display)
			})
		}
		else {
			frappe.db.get_value(frm.doc.document_type, frm.doc.document_number, ['party_type','party','shipping_address'], function (d) {
				frm.set_value('party_type', d.party_type)
				frm.set_value('party', d.party)
				frm.set_value('shipping_address', d.shipping_address)
			})
		}
	}
})
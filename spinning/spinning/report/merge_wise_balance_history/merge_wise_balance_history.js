// Copyright (c) 2016, FinByz Tech Pvt Ltd and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Merge Wise Balance History"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "80",
			"default": frappe.sys_defaults.year_start_date,
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"width": "80",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname":"item_code",
			"label": __("Item Code"),
			"fieldtype": "Link",
			"options": 'Item',
			"width": "80"
		},
		{
			"fieldname":"warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"options": 'Warehouse',
			"width": "80",
			"default": "Texturising Divison - HI",
			get_query: () => {
				let company = frappe.query_report.get_filter_value('company');
				if (company != ""){
					return {
						filters: {
							'company': company
						}
					}
				}
			}
		},
		{
			"fieldname":"item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"options": 'Item Group',
			"width": "80"
		},
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": 'Company',
			"width": "80",
			"default": frappe.defaults.get_default('company'),
		},
	]
};

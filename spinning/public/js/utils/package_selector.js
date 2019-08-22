
PackageSelector = Class.extend({
	init: function (opts) {
		$.extend(this, opts);
		this.setup();
	},

	setup: function(){
		this.set_variables();
		this.make_dialog();
	},

	set_variables: function() {
		this.warehouse = this.warehouse ? this.warehouse : (this.frm.doc.s_warehouse ? this.frm.doc.s_warehouse : this.frm.doc.warehouse);
		this.merge = this.merge ? this.merge : this.frm.doc.merge;
	},

	make_dialog: function(){
		let me = this;

		let fields = [
			{
				label: __("Source Warehouse"),
				fieldtype:'Link',
				fieldname: 'warehouse',
				options: 'Warehouse',
				default: me.warehouse,
				read_only: 1,
			},
			{
				label: __('Item Code'),
				fieldtype:'Link',
				fieldname: 'item_code',
				options: 'Item',
				default: me.item_code,
				read_only: me.item_code ? 1 : 0,
				get_query: function(){
					let items = [...new Set((me.frm.doc.items || []).map(function(i){return i.item_code}))]
					return {
						filters: {
							"item_code": ['in', items]
						}
					}
				},
				change: function(){
					let item_code = this.get_value();


					let filters = {
						'warehouse': me.warehouse,
						'merge': me.merge,
					}

					if(item_code){
						filters['item_code'] = item_code
					}

					me.set_package_data(filters)
				}
			},
			{fieldtype:'Column Break'},
			{
				label: __("Merge"),
				fieldtype:'Link',
				fieldname: 'merge',
				options: 'Merge',
				default: me.merge,
				read_only: me.merge ? 1 : 0,
			},
			{
				label: __("Grade"),
				fieldtype:'Link',
				fieldname: 'grade',
				options: 'Grade',
				change: function(){
					let grade = this.get_value();
					let item_code = me.item_code || this.layout.get_value('item_code');

					let filters = {
						'warehouse': me.warehouse,
						'merge': me.merge,
					}

					if(item_code){
						filters['item_code'] = item_code
					}

					if(grade){
						filters['grade'] = grade
					}

					me.set_package_data(filters)
				}
			},
			{fieldtype:'Column Break'},
			{
				label: __("Total Qty"),
				fieldtype: 'Float',
				fieldname: 'total_qty',
				default: '0.0',
				read_only: 1,
			},
			{
				label: __("Paper Tube"),
				fieldtype:'Link',
				fieldname: 'paper_tube',
				options: 'Item',
				get_query: function(){
					return {
						filters: {
							'item_group': "Paper Tube"
						}
					}
				}
			},
			
		]

		fields = fields.concat(this.get_package_fields());

		this.dialog = new frappe.ui.Dialog({
			title: __("Add Packages"),
			fields: fields,
		});

		let filters = {
			'item_code': this.item_code,
			'warehouse': this.warehouse,
			'merge': this.merge,
		}

		this.set_package_data(filters);

		this.dialog.set_primary_action(__("Add"), function(){
			me.values = me.dialog.get_values();
			me.set_packages();			
			me.dialog.hide();
		});

		let $package_wrapper = this.get_package_wrapper()

		$($package_wrapper).find('.grid-remove-rows').hide();
		$($package_wrapper).find('.grid-add-row').hide();

		this.dialog.show();

		this.bind_events();
	},

	bind_events: function($wrapper) {
		let me = this;

		let $package_wrapper = me.get_package_wrapper();

		$package_wrapper.on('click', '.grid-row-check:checkbox', (e) => {

			let packages = me.dialog.get_value('packages');
			let total_qty = 0;

			$.each($package_wrapper.find('.form-grid > .grid-body > .rows > .grid-row'), function (idx, row) {
				var selected_package = $(row).find('.grid-row-check:checkbox');

				if($(selected_package).is(':checked')){
					let package = packages[idx];
					total_qty += package.net_weight;
				}
			});

			me.dialog.set_value('total_qty', total_qty)
		})
	},

	get_package_wrapper: function(){
		return this.dialog.get_field('packages').$wrapper;
	},

	// validate: function(){
	// 	let values = this.values;

	// 	values.packages.map((row, i) => {
	// 		let package = row.package;

	// 		if(this.package_exists(package)){
	// 			frappe.throw(__(`Package ${package} already selected! Please select another package.`));
	// 			return false;
	// 		}
	// 	});

	// 	return true;
	// },

	package_exists: function(package){
		const packages = this.frm.doc.packages.map(data => data.package);
		return (packages && in_list(packages, package)) ? true : false;
	},

	set_packages: function () {
		let me = this;

		let packages = me.dialog.get_value('packages');
		let $result = me.dialog.get_field('packages').$wrapper;

		$.each($result.find('.form-grid > .grid-body > .rows > .grid-row'), function (idx, row) {
			var $selected_packages = $(row).find('.grid-row-check:checkbox:checked');

			if($selected_packages.length){
				let package = packages[idx];
				me.frm.add_child('packages', package);
			}
		});

		refresh_field('packages');
	},

	get_package_fields: function(){
		let me = this;

		return [
			{ fieldtype: 'Section Break', label: __('Packages') },
			{
				fieldname: 'packages',
				label: __("Packages"),
				fieldtype: "Table",
				read_only: 1,
				fields:[
					{
						'label': 'Package',
						'fieldtype': 'Link',
						'fieldname': 'package',
						'options': 'Package',
						'read_only': 1,
						'in_list_view': 1,
					},
					{
						'label': 'Spools',
						'fieldtype': 'Int',
						'fieldname': 'spools',
						'read_only': 1,
						'in_list_view': 1,
					},
					{
						'label': 'Item Code',
						'fieldtype': 'Link',
						'fieldname': 'item_code',
						'options': 'Item',
						'read_only': 1,
					},
					{
						'label': 'Item Name',
						'fieldtype': 'Data',
						'fieldname': 'item_name',
						'read_only': 1,
					},
					{
						'label': 'Warehouse',
						'fieldtype': 'Link',
						'fieldname': 'warehouse',
						'options': 'Warehouse',
						'read_only': 1,
					},
					{
						'label': 'Batch No',
						'fieldtype': 'Link',
						'fieldname': 'batch_no',
						'options': 'Batch',
						'read_only': 1,
					},
					{
						'label': 'Merge',
						'fieldtype': 'Link',
						'fieldname': 'merge',
						'options': 'Merge',
						'read_only': 1,
					},
					{
						'label': 'Grade',
						'fieldtype': 'Link',
						'fieldname': 'grade',
						'options': 'Grade',
						'read_only': 1,
					},
					{
						'label': 'Gross Weight',
						'fieldtype': 'Float',
						'fieldname': 'gross_weight',
						'read_only': 1,
						'in_list_view': 1,
					},
					{
						'label': 'Net Weight',
						'fieldtype': 'Float',
						'fieldname': 'net_weight',
						'read_only': 1,
						'in_list_view': 1,
					},
					{
						'label': 'Tare Weight',
						'fieldtype': 'Float',
						'fieldname': 'tare_weight',
						'read_only': 1,
					},
				],
				in_place_edit: true,
				// data: me.set_package_data(filters),
				get_data: function(){
					return //me.set_package_data(filters);
				}
			}
		]
	},

	set_package_data: function(filters){
		let me = this;

		frappe.call({
			method: "spinning.spinning.doctype.package.package.get_packages",
			freeze: true,
			args: {
				'filters': filters
			},
			callback: function(r){
				me.dialog.fields_dict.packages.grid.df.data = r.message;
				me.dialog.fields_dict.packages.grid.refresh();
			},
		});
	}
});

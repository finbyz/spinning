function get_merge_wise_package_details(batch_no, warehouse) {
	let template = `
		<table class="table table-bordered" style="margin: 0;">
			<thead>
				<th>{{ __("Package No") }}</th>
				<th>{{ __("Package Name") }}</th>
				<th>{{ __("Type") }}</th>
				<th>{{ __("Spools") }}</th>
				<th>{{ __("Gross Weight") }}</th>
				<th>{{ __("Net Weight") }}</th>
				<th>{{ __("Reamining Qty") }}</th>
				<th>{{ __("Status") }}</th>
			</thead>
			<tbody>
				{% for (let row of data ) { %}
					<tr>
						<td>{{ __(row['package_no']) }}</td>
						<td>{{ __(row['name']) }}</td>
						<td>{{ __(row['package_type']) }}</td>
						<td>{{ __(row['spools']) }}</td>
						<td>{{ __(row['gross_weight']) }}</td>
						<td>{{ __(row['net_weight']) }}</td>
						<td>{{ __(row['remaining_qty']) }}</td>
						<td>{{ __(row['status']) }}</td>
						
					</tr>
				{% } %}
			</tbody>
		</table>`;

		frappe.call({
		method: "spinning.api.get_merge_wise_package_details",
		args: {
			batch_no: batch_no,
			warehouse: warehouse
		},
		callback: function(r){
			let message = frappe.template.compile(template)({'data': r.message});
			frappe.msgprint({
				message: message, 
				title: "Package Details",
				wide: true,
			});
		}
	})
}
function get_package_details(batch_no,to_date) {
	let template = `
		<table class="table table-bordered" style="margin: 0;">
			<thead>
				<th>{{ __("Package") }}</th>
				<th>{{ __("Package Name") }}</th>
				<th>{{ __("Type") }}</th>
				<th>{{ __("Spools") }}</th>
				<th>{{ __("Gross Weight") }}</th>
				<th>{{ __("Net Weight") }}</th>
				<th>{{ __("Reamining Qty") }}</th>
			</thead>
			<tbody>
				{% for (let row of data ) { %}
					<tr>
						<td>{{ __(row[0]) }}</td>
						<td>{{ __(row[1]) }}</td>
						<td>{{ __(row[2]) }}</td>
						<td>{{ __(row[3]) }}</td>
						<td>{{ __(row[4]) }}</td>
						<td>{{ __(row[5]) }}</td>
						<td>{{ __(row[6]) }}</td>
						
					</tr>
				{% } %}
			</tbody>
		</table>`;

	frappe.call({
		method: "spinning.api.get_package_details",
		args: {
			batch_no: batch_no,
			to_date: to_date,
		},
		callback: function(r){
			let message = frappe.template.compile(template)({'data': r.message});
			console.log(r.message);	
			frappe.msgprint({
				message: message, 
				title: "Package Details",
				wide: true,
			});
		}
	})
}
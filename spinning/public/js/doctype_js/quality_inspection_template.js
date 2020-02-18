frappe.ui.form.on("Quality Inspection Template", {
    quality_inspection_name: function(frm){
        frm.clear_table("item_quality_inspection_parameter");
        frappe.model.with_doc("Quality Inspection Template", frm.doc.quality_inspection_name, function() {
            var qmtable= frappe.model.get_doc("Quality Inspection Template", frm.doc.quality_inspection_name)
            $.each(qmtable.item_quality_inspection_parameter, function(index, row){
                let d = frm.add_child("item_quality_inspection_parameter");
                d.specification=row.specification;
                d.value= row.value;
            })
        });
        frm.refresh_field('item_quality_inspection_parameter');
    },
});
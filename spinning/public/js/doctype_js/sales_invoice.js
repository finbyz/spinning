this.frm.add_fetch('batch_no', 'merge', 'merge');
this.frm.add_fetch('batch_no', 'grade', 'grade');

this.frm.cscript.onload = function (frm) {
    this.frm.set_query("batch_no", "items", function (doc, cdt, cdn) {
        let d = locals[cdt][cdn];

        if (!d.item_code) {
            frappe.throw(__("Please enter Item Code to get batch no."));
        }
        else {
            return {
                query: "spinning.api.get_batch_no",
                filters: {
                    'item_code': d.item_code,
                    'warehouse': d.warehouse
                }
            }
        }
    });
}
frappe.ui.form.on("Sales Invoice", {
    refresh: function(frm){
        frm.set_df_property("company", "read_only", (!frm.doc.__islocal || frm.doc.amended_from) ? 1 : 0);
    },
    onload: function (frm) {
        frm.trigger("set_default_bank_account");
        frm.trigger("set_insurance_detail");
    },
    company: function (frm) {
        frm.trigger("set_default_bank_account");
        frm.trigger("set_insurance_detail");
    },
    set_insurance_detail: function (frm) {
        if (!frm.doc.insurance_detail && frm.doc.docstatus != 1) {
            frappe.db.get_value("Company", frm.doc.company, 'insurance_detail', function (r) {
                if (r.insurance_detail) {
                    frm.set_value("insurance_detail", r.insurance_detail)
                }
            })
        }
    },
    set_default_bank_account: function (frm) {
        frappe.db.get_value("Bank Account", { 'is_default': 1, 'is_company_account': 1, 'company': frm.doc.company }, 'name', function (r) {
            if (r.name) {
                frm.set_value('bank_account', r.name)
            }
        })
    }
});
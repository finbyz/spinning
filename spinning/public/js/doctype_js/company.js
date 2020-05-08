cur_frm.fields_dict.pallet_in_use.get_query = function (doc) {
    return {
        filters: {
            "company": doc.name
        }
    }
};
cur_frm.fields_dict.pallet_out.get_query = function (doc) {
    return {
        filters: {
            "company": doc.name
        }
    }
};
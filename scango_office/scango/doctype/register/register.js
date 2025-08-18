// Copyright (c) 2025, kunpriya-natpaphat and contributors
// For license information, please see license.txt
frappe.ui.form.on("Register", {
    refresh: function(frm) {
        calculate_age(frm);
        toggle_other_gender_details(frm);
        set_gender_automatically(frm);
    },
    date_of_birth: function(frm) {
        calculate_age(frm);
    },
    gender: function(frm) {
        toggle_other_gender_details(frm);
    },
    salutation: function(frm) {
        set_gender_automatically(frm);
    }
});
function calculate_age(frm) {
    if (frm.doc.date_of_birth) {
        let dob = frappe.datetime.str_to_obj(frm.doc.date_of_birth);
        let today = new Date();
        let age = today.getFullYear() - dob.getFullYear();
        let m = today.getMonth() - dob.getMonth();
        if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
            age--;
        }
        frm.set_value('calculated_age', age);
    } else {
        frm.set_value('calculated_age', null);
    }
}
function toggle_other_gender_details(frm) {
    if (frm.doc.gender === 'อื่นๆ') {
        frm.toggle_req('other_gender_details', true);
        frm.set_df_property('other_gender_details', 'hidden', false);
    } else {
        frm.toggle_req('other_gender_details', false);
        frm.set_df_property('other_gender_details', 'hidden', true);
        frm.set_value('other_gender_details', null);
    }
}
function set_gender_automatically(frm) {
    let salutation = frm.doc.salutation;
    let gender_value = null;

    if (salutation) {
        switch (salutation) {
            case 'นาย':
            case 'เด็กชาย':
            case 'Mr.':
            case 'Master':
                gender_value = 'ชาย';
                break;
            case 'นาง':
            case 'นางสาว':
            case 'เด็กหญิง':
            case 'Miss':
            case 'Mrs.':
                gender_value = 'หญิง';
                break;
            default:
                gender_value = null;
                break;
        }
    }
    if (frm.doc.gender !== gender_value) {
        frm.set_value('gender', gender_value);
    }
}
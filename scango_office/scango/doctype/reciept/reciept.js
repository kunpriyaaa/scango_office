// Copyright (c) 2025, kunpriya-natpaphat and contributors
// For license information, please see license.txt
frappe.ui.form.on("Receipt", {
    refresh(frm) {
        console.log("Receipt refresh")
    },
});
 
frappe.ui.form.on('ReceiptProductDetails', {
    quantity: calculate_detail_total,
    product_price: calculate_detail_total
});
 
function calculate_detail_total(frm, cdt, cdn) {
    try {
        let row = frappe.get_doc(cdt, cdn);
        let quantity = parseFloat(row.quantity) || 0;
        let product_price = parseFloat(row.product_price) || 0;
 
        if ('total' in row) {
            row.total = quantity * product_price
        }
        //refresh fields
        frm.refresh_field(row.parentfield)
 
        //calculate net total
        calculate_net_total(frm, cdt, cdn)
    } catch (error) {
        console.error("Error updating total in Receipt Product Detail:", error);
        frappe.msgprint(__('An error occurred while calculating the total.'));
 
    }
}
 
function calculate_net_total(frm, cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    let parentfield = row.parentfield
    // console.log(frm.doc[row.parentfield])
   
    let total_sum = 0;
    frm.doc[row.parentfield].forEach(row => {
        total_sum += row.total || 0;
    });
 
    // Optionally set this sum to a field in the parent doctype
    frm.set_value('net_total', total_sum);
 
}
 
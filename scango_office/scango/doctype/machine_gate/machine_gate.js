// Copyright (c) 2025, kunpriya-natpaphat and contributors
// For license information, please see license.txt

frappe.ui.form.on("Machine Gate", {
    refresh(frm) {
        frm.add_custom_button('Open Gate Scanner', () => {
            window.open(`/gate?name=${frm.doc.name}`, '_blank');  // Opens in a new tab
        });

    },
});

// Copyright (c) 2025, kunpriya-natpaphat and contributors
// For license information, please see license.txt

frappe.ui.form.on("Security Status Dashboard", {
    refresh(frm) {
        // อัพเดตข้อมูล Dashboard เมื่อเปิดหน้า
        update_dashboard_data(frm);
    }
});

function update_dashboard_data(frm) {
    // เรียก Server Method เพื่ออัพเดตข้อมูล
    frappe.call({
        method: "frappe.client.get_count",
        args: {
            doctype: "SecurityPersonnel",
            filters: {
                "employment_status": "ปฏิบัติงาน"
            }
        },
        callback: function(r) {
            if (r.message) {
                frm.set_value("active_count", r.message);
            }
        }
    });

    // นับจำนวนรปภ พักงาน/ลางาน
    frappe.call({
        method: "frappe.client.get_count", 
        args: {
            doctype: "SecurityPersonnel",
            filters: {
                "employment_status": ["in", ["พักงาน", "ลางาน"]]
            }
        },
        callback: function(r) {
            if (r.message) {
                frm.set_value("inactive_count", r.message);
            }
        }
    });

    // นับจำนวนรปภ ทั้งหมด
    frappe.call({
        method: "frappe.client.get_count",
        args: {
            doctype: "SecurityPersonnel"
        },
        callback: function(r) {
            if (r.message) {
                frm.set_value("total_count", r.message);
            }
        }
    });

    // นับจำนวนอาคารเปิดให้ผู้เยี่ยม
    frappe.call({
        method: "frappe.client.get_count",
        args: {
            doctype: "Building Management",
            filters: {
                "is_visitor_accessible": 1,
                "status": "เปิดใช้งาน"
            }
        },
        callback: function(r) {
            if (r.message) {
                frm.set_value("accessible_buildings_count", r.message);
            }
        }
    });

    // อัพเดตเวลา
    frm.set_value("last_updated", frappe.datetime.now_datetime());
}
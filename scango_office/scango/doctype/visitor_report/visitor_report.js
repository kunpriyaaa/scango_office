// Copyright (c) 2025, kunpriya-natpaphat and contributors
// For license information, please see license.txt

frappe.ui.form.on('Visitor Report', {
    refresh: function(frm) {
        // เพิ่มปุ่มสร้างรายงาน
        frm.add_custom_button('สร้างรายงาน', function() {
            generate_visitor_report(frm);
        }, 'Actions');
    }
});

function generate_visitor_report(frm) {
    // แสดง loading
    frm.set_value('report_data', '<div class="text-center"><i class="fa fa-spinner fa-spin"></i> กำลังสร้างรายงาน...</div>');
    frm.refresh_field('report_data');

    // ตรวจสอบ DocType ที่มีอยู่จริง
    let possible_doctypes = ['Visitor Management', 'Visitor', 'VisitorManagement', 'Visitor Request'];
    
    check_available_doctype(possible_doctypes, 0, frm);
}

function check_available_doctype(doctypes, index, frm) {
    if (index >= doctypes.length) {
        // ไม่พบ DocType ใดเลย
        frm.set_value('report_data', `
            <div class="alert alert-danger">
                <h5>ไม่พบ DocType!</h5>
                <p>ไม่พบ DocType สำหรับข้อมูลผู้เยี่ยม</p>
                <small>ตรวจสอบแล้ว: ${doctypes.join(', ')}</small>
            </div>
        `);
        return;
    }

    let current_doctype = doctypes[index];
    
    // ทดสอบเรียกข้อมูล
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: current_doctype,
            fields: ['name'],
            limit_page_length: 1
        },
        callback: function(r) {
            if (r.message !== undefined) {
                // พบ DocType ที่ใช้งานได้
                console.log('Found working DocType:', current_doctype);
                load_visitor_data(frm, current_doctype);
            } else {
                // ลอง DocType ถัดไป
                check_available_doctype(doctypes, index + 1, frm);
            }
        },
        error: function() {
            // ลอง DocType ถัดไป
            check_available_doctype(doctypes, index + 1, frm);
        }
    });
}

function load_visitor_data(frm, doctype_name) {
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: doctype_name,
            filters: get_filters(frm),
            fields: [
                'name', 'visitor_name', 'visitor_phone', 'company', 
                'visit_date', 'visit_time', 'purpose', 'building', 
                'status', 'approved_by', 'check_in_time', 'check_out_time',
                'creation'
            ],
            order_by: 'creation desc',
            limit_page_length: 1000
        },
        callback: function(r) {
            if (r.message) {
                let visitors = r.message;
                frm.set_value('total_visitors', visitors.length);
                
                let html = generate_table_html(visitors, doctype_name);
                frm.set_value('report_data', html);
                frm.set_value('report_status', 'Generated');
                
                // แสดงข้อความสำเร็จ
                frappe.show_alert({
                    message: `สร้างรายงานสำเร็จ! DocType: ${doctype_name}, พบ ${visitors.length} รายการ`,
                    indicator: 'green'
                });
                
                frm.save();
            } else {
                frm.set_value('report_data', `
                    <div class="alert alert-info">
                        <p>ไม่พบข้อมูลผู้เยี่ยมในระบบ</p>
                        <small>DocType: ${doctype_name}</small>
                    </div>
                `);
                frm.set_value('total_visitors', 0);
                frm.set_value('report_status', 'Generated');
            }
        },
        error: function(r) {
            frm.set_value('report_data', `
                <div class="alert alert-danger">
                    <h5>เกิดข้อผิดพลาด!</h5>
                    <p>ไม่สามารถดึงข้อมูลจาก ${doctype_name}</p>
                    <pre>${r.exc || 'Unknown error'}</pre>
                </div>
            `);
            frm.set_value('report_status', 'Error');
        }
    });
}

function get_filters(frm) {
    let filters = {};
    
    // กรองวันที่
    if (frm.doc.date_from && frm.doc.date_to) {
        filters['visit_date'] = ['between', [frm.doc.date_from, frm.doc.date_to]];
    } else if (frm.doc.date_from) {
        filters['visit_date'] = ['>=', frm.doc.date_from];
    } else if (frm.doc.date_to) {
        filters['visit_date'] = ['<=', frm.doc.date_to];
    }
    
    // กรองสถานะ
    if (frm.doc.status_filter && frm.doc.status_filter !== 'ทั้งหมด') {
        filters['status'] = frm.doc.status_filter;
    }
    
    // กรองอาคาร
    if (frm.doc.building_filter) {
        filters['building'] = frm.doc.building_filter;
    }
    
    // กรองรปภ
    if (frm.doc.security_personnel_filter) {
        filters['approved_by'] = frm.doc.security_personnel_filter;
    }
    return filters;
}

function generate_table_html(visitors, doctype_name) {
    if (!visitors || visitors.length === 0) {
        return `
            <div class="alert alert-info">
                <h5>ไม่พบข้อมูลผู้เยี่ยม</h5>
                <p>ไม่พบข้อมูลผู้เยี่ยมตามเงื่อนไขที่กำหนด</p>
                <small>DocType: ${doctype_name}</small>
            </div>
        `;
    }
    
    let html = `
        <div class="mb-2">
            <small class="text-muted">
                📋 DocType: <strong>${doctype_name}</strong> | 
                📊 จำนวน: <strong>${visitors.length}</strong> รายการ |
                🕐 ${new Date().toLocaleString('th-TH')}
            </small>
        </div>
        
        <table class="table table-bordered table-striped table-hover">
            <thead class="table-dark">
                <tr>
                    <th>รหัส</th>
                    <th>ชื่อผู้เยี่ยม</th>
                    <th>โทรศัพท์</th>
                    <th>บริษัท</th>
                    <th>วันที่เยี่ยม</th>
                    <th>เวลา</th>
                    <th>วัตถุประสงค์</th>
                    <th>อาคาร</th>
                    <th>สถานะ</th>
                    <th>อนุมัติโดย</th>
                    <th>เวลาเข้า</th>
                    <th>เวลาออก</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    visitors.forEach((visitor, index) => {
        const status_badge = get_status_badge(visitor.status);
        
        html += `
            <tr>
                <td><small>${visitor.name || ''}</small></td>
                <td><strong>${visitor.visitor_name || ''}</strong></td>
                <td>${visitor.visitor_phone || ''}</td>
                <td><small>${visitor.company || ''}</small></td>
                <td><small>${visitor.visit_date || ''}</small></td>
                <td><small>${visitor.visit_time || ''}</small></td>
                <td><small>${visitor.purpose || ''}</small></td>
                <td><small>${visitor.building || ''}</small></td>
                <td>${status_badge}</td>
                <td><small>${visitor.approved_by || ''}</small></td>
                <td><small>${visitor.check_in_time || ''}</small></td>
                <td><small>${visitor.check_out_time || ''}</small></td>
            </tr>
        `;
    });
    
    html += `
            </tbody>
        </table>
        <div class="mt-2">
            <small class="text-muted">
                📈 แสดงข้อมูลล่าสุด ${visitors.length} รายการ (จำกัดไม่เกิน 1,000 รายการ)
            </small>
        </div>
    `;
    
    return html;
}

function get_status_badge(status) {
    if (!status) {
        return "<span class='badge bg-secondary'>-</span>";
    }
        
    const badges = {
        "รออนุมัติ": "<span class='badge bg-warning text-dark'>รออนุมัติ</span>",
        "อนุมัติ": "<span class='badge bg-success'>อนุมัติ</span>",
        "ปฏิเสธ": "<span class='badge bg-danger'>ปฏิเสธ</span>",
        "เข้าแล้ว": "<span class='badge bg-info'>เข้าแล้ว</span>",
        "ออกแล้ว": "<span class='badge bg-secondary'>ออกแล้ว</span>",
        // English versions
        "Draft": "<span class='badge bg-light text-dark'>Draft</span>",
        "Pending": "<span class='badge bg-warning text-dark'>Pending</span>",
        "Approved": "<span class='badge bg-success'>Approved</span>",
        "Rejected": "<span class='badge bg-danger'>Rejected</span>",
        "Checked In": "<span class='badge bg-info'>Checked In</span>",
        "Checked Out": "<span class='badge bg-secondary'>Checked Out</span>"
    };
    
    return badges[status] || `<span class='badge bg-light text-dark'>${status}</span>`;
}
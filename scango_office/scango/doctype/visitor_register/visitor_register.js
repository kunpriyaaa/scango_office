// Copyright (c) 2025, kunpriya-natpaphat and contributors
// For license information, please see license.txt

frappe.ui.form.on("Visitor Register", {
    refresh: function(frm) {
        calculate_age(frm);
        set_gender_automatically(frm);
        set_birth_date_max(frm);
        setup_id_field_formatting(frm);
        toggle_other_purpose_details(frm);
    },
    
    birth_date: function(frm) {
        calculate_age(frm);
        validate_birth_date(frm);
    },
    
    gender: function(frm) {
        // Mark that gender was manually changed
        frm._gender_manually_set = true;
    },
    
    salutation: function(frm) {
        // Only auto-set gender if gender is not already set
        if (!frm.doc.gender || frm.doc.gender === 'ไม่ระบุ') {
            set_gender_automatically(frm);
        }
    },

    visit_date: function(frm) {
        calculate_visit_duration(frm);
    },

    visit_end_date: function(frm) {
        calculate_visit_duration(frm);
    },

    purpose: function(frm) {
        toggle_other_purpose_details(frm);
    },

    visitor_photo: function(frm) {
        check_and_generate_qr_code(frm);
    },

    terms_accepted: function(frm) {
        check_and_generate_qr_code(frm);
    },

    thai_national_id: function(frm) {
        // No validation during typing - only format/cleanup if needed
    },

    passport_number: function(frm) {
        // Only format to uppercase
        format_passport_number(frm);
    }
});

function calculate_age(frm) {
    if (frm.doc.birth_date) {
        let dob = frappe.datetime.str_to_obj(frm.doc.birth_date);
        let today = new Date();
        
        // Check if date is in future
        if (dob > today) {
            frm.set_value('age', '');
            return;
        }
        
        let age = today.getFullYear() - dob.getFullYear();
        let month_diff = today.getMonth() - dob.getMonth();
        
        // If birth month hasn't occurred this year, or 
        // birth month is current month but birth day hasn't occurred, subtract 1
        if (month_diff < 0 || (month_diff === 0 && today.getDate() < dob.getDate())) {
            age--;
        }
        
        // Ensure age is not negative
        if (age < 0) age = 0;
        
        frm.set_value('age', age);
    } else {
        frm.set_value('age', '');
    }
}

function validate_birth_date(frm) {
    if (frm.doc.birth_date) {
        let today = frappe.datetime.get_today();
        if (frm.doc.birth_date > today) {
            frappe.msgprint({
                title: 'วันที่ไม่ถูกต้อง',
                message: 'ไม่สามารถเลือกวันที่ในอนาคตได้',
                indicator: 'red'
            });
            frm.set_value('birth_date', '');
            frm.set_value('age', '');
        }
    }
}

function set_birth_date_max(frm) {
    // Prevent future dates
    let today = frappe.datetime.get_today();
    frm.set_df_property('birth_date', 'options', {
        maxDate: today
    });
}

function toggle_other_gender_details(frm) {
    if (frm.doc.gender === 'อื่นๆ') {
        frm.set_df_property('other_gender_details', 'reqd', 1);
        frm.set_df_property('other_gender_details', 'hidden', 0);
    } else {
        frm.set_df_property('other_gender_details', 'reqd', 0);
        frm.set_df_property('other_gender_details', 'hidden', 1);
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
                gender_value = 'ชาย';
                break;
            case 'นาง':
            case 'นางสาว':
            case 'เด็กหญิง':
            case 'Ms.':
            case 'Mrs.':
                gender_value = 'หญิง';
                break;
            default:
                gender_value = 'ไม่ระบุ';
                break;
        }
    }
    
    // Only set if different and not manually changed
    if (gender_value && frm.doc.gender !== gender_value && !frm._gender_manually_set) {
        frm.set_value('gender', gender_value);
    }
}

function calculate_visit_duration(frm) {
    if (frm.doc.visit_date && frm.doc.visit_end_date) {
        let start_date = frappe.datetime.str_to_obj(frm.doc.visit_date);
        let end_date = frappe.datetime.str_to_obj(frm.doc.visit_end_date);
        
        // Validate that end date is not before start date
        if (end_date < start_date) {
            frappe.msgprint({
                title: 'วันที่ไม่ถูกต้อง',
                message: 'วันที่ออกต้องไม่เป็นวันก่อนวันที่เข้า',
                indicator: 'red'
            });
            frm.set_value('visit_end_date', '');
            frm.set_value('total_days', '');
            return;
        }
        
        // Calculate duration in days
        let duration = Math.ceil((end_date - start_date) / (1000 * 60 * 60 * 24)) + 1; // +1 to include both start and end dates
        frm.set_value('total_days', duration);
    } else {
        frm.set_value('total_days', '');
    }
}

function toggle_other_purpose_details(frm) {
    if (frm.doc.purpose === 'อื่นๆ') {
        frm.set_df_property('other_purpose_details', 'reqd', 1);
        frm.set_df_property('other_purpose_details', 'hidden', 0);
    } else {
        frm.set_df_property('other_purpose_details', 'reqd', 0);
        frm.set_df_property('other_purpose_details', 'hidden', 1);
        frm.set_value('other_purpose_details', null);
    }
}

function check_and_generate_qr_code(frm) {
    // Silently check if required fields for QR generation are completed
    // QR code will be generated automatically on server-side without notification
}

function generate_qr_code(frm) {
    if (!frm.doc.name || frm.doc.__islocal) {
        // Document needs to be saved first
        frappe.msgprint({
            title: 'จำเป็นต้องบันทึกข้อมูลก่อน',
            message: 'กรุณาบันทึกข้อมูลก่อนสร้าง QR Code',
            indicator: 'blue'
        });
        return;
    }

    // Generate QR code content
    let qr_data = {
        visitor_id: frm.doc.name,
        full_name: (frm.doc.first_name || '') + ' ' + (frm.doc.last_name || ''),
        visit_date: frm.doc.visit_date,
        visit_end_date: frm.doc.visit_end_date,
        purpose: frm.doc.purpose,
        phone: frm.doc.phone_number,
        generated_at: frappe.datetime.now_datetime()
    };
    
    // Create QR code string
    let qr_string = JSON.stringify(qr_data);
    
    // Set QR code (in real implementation, you might use a QR library or server-side generation)
    frm.set_value('qr_code', qr_string);
    
    frappe.msgprint({
        title: 'QR Code สร้างเรียบร้อย',
        message: 'QR Code สำหรับผู้เยี่ยมชมได้ถูกสร้างแล้ว',
        indicator: 'green'
    });
}

function setup_id_field_formatting(frm) {
    // Setup validation for Thai National ID
    if (frm.fields_dict.thai_national_id) {
        frm.fields_dict.thai_national_id.$input.on('keypress', function(e) {
            var charCode = (e.which) ? e.which : e.keyCode;
            // Block non-numeric characters
            if (charCode > 31 && (charCode < 48 || charCode > 57)) {
                e.preventDefault();
                return false;
            }
        });
        
        frm.fields_dict.thai_national_id.$input.on('input', function() {
            let value = $(this).val();
            // Limit to 13 digits only
            if (value.length > 13) {
                value = value.substring(0, 13);
                $(this).val(value);
            }
        });
        
        // No more blur validation - removed completely
    }

    // Setup passport number formatting  
    if (frm.fields_dict.passport_number) {
        frm.fields_dict.passport_number.$input.on('input', function() {
            let value = $(this).val().toUpperCase();
            $(this).val(value);
        });
    }
}

function validate_thai_national_id_input(frm, value) {
    if (value) {
        let numbers_only = value.replace(/\D/g, '');
        let has_invalid_chars = value !== numbers_only;
        let wrong_length = numbers_only.length !== 13;
        
        if (has_invalid_chars || wrong_length) {
            let message = '';
            if (has_invalid_chars) {
                message += 'พบอักขระที่ไม่ใช่ตัวเลข ';
            }
            if (wrong_length) {
                message += `ต้องเป็น 13 หลัก (ปัจจุบัน ${numbers_only.length} หลัก)`;
            }
            
            frappe.msgprint({
                title: 'รูปแบบเลขบัตรประชาชนไม่ถูกต้อง',
                message: message + '<br><b>ตัวอย่างที่ถูกต้อง:</b> 1234567890123',
                indicator: 'orange'
            });
        }
    }
}

function validate_passport_number_input(frm, value) {
    if (value) {
        let valid_chars = value.replace(/[^A-Z0-9]/g, '');
        let has_invalid_chars = value !== valid_chars;
        
        if (has_invalid_chars) {
            frappe.msgprint({
                title: 'รูปแบบเลขหนังสือเดินทางไม่ถูกต้อง',
                message: 'อนุญาตเฉพาะตัวอักษรอังกฤษ A-Z และตัวเลข 0-9 เท่านั้น<br><b>ตัวอย่างที่ถูกต้อง:</b> AB1234567',
                indicator: 'orange'
            });
        }
    }
}

function format_thai_national_id(frm) {
    // This function now just validates on form change, doesn't auto-format
    if (frm.doc.thai_national_id) {
        validate_thai_national_id_input(frm, frm.doc.thai_national_id);
    }
}

function format_passport_number(frm) {
    // Auto-uppercase only, keep validation separate
    if (frm.doc.passport_number) {
        let value = frm.doc.passport_number.toUpperCase();
        frm.set_value('passport_number', value);
        validate_passport_number_input(frm, value);
    }
}
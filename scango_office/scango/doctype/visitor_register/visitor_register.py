# visitor_register.py (ไฟล์เต็ม - แก้ไขแล้ว)

import frappe
from frappe.model.document import Document
import re

class VisitorRegister(Document):
    def validate(self):
        """Validate visitor register fields"""
        self.validate_name_fields()
        self.validate_id_fields()
        self.validate_birth_date()
        self.calculate_age()
        self.validate_visit_dates()
        self.calculate_visit_duration()
        self.validate_terms_acceptance()
    
    def validate_name_fields(self):
        """Validate name fields to allow only Thai and English characters"""
        name_fields = {
            'first_name': 'ชื่อ',
            'middle_name': 'ชื่อกลาง', 
            'last_name': 'นามสกุล'
        }
        
        pattern = r'^[a-zA-Zก-๙\s]+$'
        
        for field_name, label in name_fields.items():
            if self.get(field_name):
                value = self.get(field_name).strip()
                if not re.match(pattern, value):
                    frappe.throw(
                        f"ช่อง {label} สามารถกรอกได้เฉพาะตัวอักษรไทย-อังกฤษเท่านั้น",
                        title="ข้อมูลไม่ถูกต้อง"
                    )
                
                if '  ' in value or value != value.strip():
                    frappe.throw(
                        f"ช่อง {label} ไม่ควรมีช่องว่างซ้ำกันหรือเว้นวรรคหน้า-หลัง",
                        title="รูปแบบไม่ถูกต้อง"
                    )
    
    def validate_id_fields(self):
        """Validate ID number fields based on document type"""
        if not self.id_type:
            return
            
        if self.id_type == "เลขบัตรประชาชน":
            if self.thai_national_id:
                if self.flags.ignore_validate:
                    return
                self.validate_national_id()
        elif self.id_type == "เลขหนังสือเดินทาง":
            if self.passport_number:
                if self.flags.ignore_validate:
                    return
                self.validate_passport_number()
    
    def validate_national_id(self):
        """Validate Thai National ID (13 digits)"""
        national_id = self.thai_national_id.replace('-', '').replace(' ', '')
        
        if len(national_id) < 10:
            return
            
        if not national_id.isdigit() or len(national_id) != 13:
            frappe.throw(
                "เลขบัตรประชาชนต้องเป็นตัวเลข 13 หลักเท่านั้น",
                title="เลขบัตรประชาชนไม่ถูกต้อง"
            )
        
        if not self.is_valid_thai_id(national_id):
            frappe.throw(
                "เลขบัตรประชาชนไม่ถูกต้องตามหลักการคำนวณ",
                title="เลขบัตรประชาชนไม่ถูกต้อง"
            )
    
    def is_valid_thai_id(self, national_id):
        """Validate Thai National ID using checksum algorithm"""
        if len(national_id) != 13:
            return False
        
        sum_value = 0
        for i in range(12):
            sum_value += int(national_id[i]) * (13 - i)
        
        remainder = sum_value % 11
        check_digit = (11 - remainder) % 10
        
        return int(national_id[12]) == check_digit
    
    def validate_passport_number(self):
        """No validation required for passport number"""
        if self.passport_number:
            self.passport_number = self.passport_number.upper()
        return
    
    def validate_birth_date(self):
        """Validate birth date is not in the future"""
        if self.birth_date:
            from datetime import date
            from frappe.utils import getdate
            
            today = date.today()
            birth_date = getdate(self.birth_date)
            
            if birth_date > today:
                frappe.throw(
                    "วันเกิดไม่สามารถเป็นวันที่ในอนาคตได้",
                    title="วันที่ไม่ถูกต้อง"
                )
    
    def calculate_age(self):
        """Calculate age automatically from birth date"""
        if not self.birth_date:
            self.age = None
            return
        
        from datetime import date
        from frappe.utils import getdate
        
        today = date.today()
        birth_date = getdate(self.birth_date)
        
        if birth_date > today:
            self.age = None
            return
        
        age = today.year - birth_date.year
        
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        
        self.age = age

    def validate_visit_dates(self):
        """Validate visit dates"""
        from frappe.utils import getdate, today
        
        today_date = getdate(today())
        
        if self.visit_date:
            start_date = getdate(self.visit_date)
            if start_date != today_date:
                frappe.throw(
                    "วันที่เข้าต้องเป็นวันนี้เท่านั้น",
                    title="วันที่ไม่ถูกต้อง"
                )
        
        if self.visit_date and self.visit_end_date:
            start_date = getdate(self.visit_date)
            end_date = getdate(self.visit_end_date)
            
            if end_date < start_date:
                frappe.throw(
                    "วันที่ออกต้องไม่เป็นวันก่อนวันที่เข้า",
                    title="วันที่ไม่ถูกต้อง"
                )

    def calculate_visit_duration(self):
        """Calculate visit duration automatically"""
        if self.visit_date and self.visit_end_date:
            from frappe.utils import getdate, date_diff
            
            start_date = getdate(self.visit_date)
            end_date = getdate(self.visit_end_date)
            
            if end_date >= start_date:
                duration = date_diff(end_date, start_date) + 1
                self.total_days = duration
            else:
                self.total_days = None
        else:
            self.total_days = None

    def validate_terms_acceptance(self):
        """Validate that terms are accepted when visitor photo is uploaded"""
        if hasattr(self, 'visitor_photo') and hasattr(self, 'terms_accepted'):
            if self.visitor_photo and not self.terms_accepted:
                frappe.throw(
                    "กรุณายอมรับเงื่อนไขการเข้า-ออกสถานที่",
                    title="จำเป็นต้องยอมรับเงื่อนไข"
                )

    def before_save(self):
        """Clean up data and generate QR code before saving"""
        name_fields = ['first_name', 'middle_name', 'last_name']
        for field in name_fields:
            if self.get(field):
                cleaned_value = ' '.join(self.get(field).split())
                self.set(field, cleaned_value)
        
        if self.thai_national_id:
            self.thai_national_id = self.thai_national_id.replace('-', '').replace(' ', '')
        
        if self.passport_number:
            self.passport_number = self.passport_number.upper().replace(' ', '')
        
        if self.visitor_photo and self.terms_accepted:
            self.generate_qr_code()

    def generate_qr_code(self):
        """Generate QR code with visitor ID only"""
        import qrcode
        import io
        import base64
        
        if not self.name:
            return
        
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.name)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            img_buffer = io.BytesIO()
            qr_img.save(img_buffer, format='PNG')
            img_str = base64.b64encode(img_buffer.getvalue()).decode()
            
            from frappe.utils.file_manager import save_file
            file_doc = save_file(
                fname=f"qr_code_{self.name}.png",
                content=base64.b64decode(img_str),
                dt=self.doctype,
                dn=self.name,
                is_private=1
            )
            
            self.qr_code = file_doc.file_url
            
            frappe.msgprint(
                f"QR Code สร้างเรียบร้อย (ID: {self.name})",
                title="QR Code พร้อมใช้งาน",
                indicator="green"
            )
            
        except ImportError:
            frappe.msgprint(
                "กรุณาติดตั้ง: pip install qrcode[pil] เพื่อสร้าง QR Code",
                title="ต้องติดตั้ง Library",
                indicator="orange"
            )
        except Exception as e:
            frappe.log_error(f"Error generating QR Code: {str(e)}")
            frappe.msgprint(
                "เกิดข้อผิดพลาดในการสร้าง QR Code",
                title="ข้อผิดพลาด",
                indicator="red"
            )


# ==================== Gate Pass Functions ====================

@frappe.whitelist()
def check_qr_status(visitor_id):
    """Check if visitor can check in (not checked out yet)"""
    try:
        visitor = frappe.get_doc("Visitor Register", visitor_id)
        
        # ตรวจสอบว่ามี Checkout record หรือยัง (ตรวจสอบเข้มงวด)
        checkout_records = frappe.get_all("Visitor Gate Pass", 
            filters={
                "visitor_register": visitor_id,
                "action_type": "Checkout"
            },
            limit=1
        )
        
        if checkout_records:
            return {
                "valid": False,
                "message": "QR Code นี้ถูกใช้ Checkout ไปแล้ว ไม่สามารถใช้งานอีกได้",
                "status": "checked_out",
                "checkout_time": checkout_records[0].get("scan_datetime")
            }
        
        # ตรวจสอบวันหมดอายุ
        from frappe.utils import getdate, today
        today_date = getdate(today())
        
        if visitor.visit_date:
            start_date = getdate(visitor.visit_date)
            if today_date < start_date:
                return {
                    "valid": False,
                    "message": "QR Code ยังไม่ถึงวันที่ใช้งาน",
                    "status": "not_started"
                }
        
        if visitor.visit_end_date:
            end_date = getdate(visitor.visit_end_date)
            if today_date > end_date:
                return {
                    "valid": False,
                    "message": "QR Code หมดอายุแล้ว",
                    "status": "expired"
                }
        
        return {
            "valid": True,
            "message": "QR Code ใช้งานได้",
            "status": "active",
            "visitor": visitor.as_dict()
        }
        
    except frappe.DoesNotExistError:
        return {
            "valid": False,
            "message": "ไม่พบข้อมูลผู้เยี่ยมชม",
            "status": "not_found"
        }
    except Exception as e:
        frappe.log_error(f"Check QR Status Error: {str(e)}")
        return {
            "valid": False,
            "message": f"เกิดข้อผิดพลาด: {str(e)}",
            "status": "error"
        }


@frappe.whitelist()
def process_gate_scan(visitor_id, gate_machine, building_gate, building_name, action_type):
    """
    Process QR scan at gate
    action_type: 'In', 'Out', 'CheckStatus', หรือ 'Checkout'
    """
    try:
        # ตรวจสอบสถานะ QR ก่อนเสมอ (ยกเว้น CheckStatus)
        status = check_qr_status(visitor_id)
        
        # ถ้าเป็น CheckStatus ให้ดูสถานะอย่างเดียว ไม่บันทึก
        if action_type == "CheckStatus":
            return status
        
        # สำหรับ In, Out, Checkout - ต้อง valid เท่านั้น
        if not status["valid"]:
            # ห้ามบันทึก gate pass ถ้า QR ไม่ valid
            frappe.throw(status["message"], title="QR Code ไม่สามารถใช้งานได้")
        
        visitor = frappe.get_doc("Visitor Register", visitor_id)
        
        # บันทึกการแสกนใน Visitor Gate Pass
        gate_pass = frappe.get_doc({
            "doctype": "Visitor Gate Pass",
            "visitor_register": visitor_id,
            "visitor_name": visitor.first_name or "",
            "visitor_last_name": visitor.last_name or "",
            "gate_machine": gate_machine,
            "building_gate": building_gate,
            "building_name": building_name,
            "action_type": action_type,
            "scan_datetime": frappe.utils.now_datetime()
        })
        gate_pass.insert(ignore_permissions=True)
        frappe.db.commit()
        
        messages = {
            "In": "เข้าสถานที่สำเร็จ",
            "Out": "ออกจากสถานที่สำเร็จ",
            "Checkout": "Checkout สำเร็จ - QR Code ถูกปิดการใช้งานถาวร"
        }
        
        return {
            "valid": True,
            "message": messages.get(action_type, "บันทึกสำเร็จ"),
            "status": "success",
            "action_type": action_type,
            "visitor": visitor.as_dict(),
            "gate_pass": gate_pass.name
        }
        
    except Exception as e:
        frappe.log_error(f"Gate Scan Error: {str(e)}")
        return {
            "valid": False,
            "message": f"เกิดข้อผิดพลาด: {str(e)}",
            "status": "error"
        }


@frappe.whitelist()
def get_gate_pass_history(visitor_id):
    """Get all gate pass history for a visitor"""
    try:
        history = frappe.get_all("Visitor Gate Pass",
            filters={"visitor_register": visitor_id},
            fields=["name", "visitor_name", "visitor_last_name", "gate_machine", 
                    "building_gate", "building_name", "action_type", "scan_datetime"],
            order_by="scan_datetime desc"
        )
        
        return {
            "success": True,
            "history": history,
            "total_scans": len(history)
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }
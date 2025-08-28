# Copyright (c) 2024, Scango and contributors
# For license information, please see license.txt

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
        
        # Pattern for Thai and English characters only (including spaces)
        pattern = r'^[a-zA-Zก-๙\s]+$'
        
        for field_name, label in name_fields.items():
            if self.get(field_name):
                value = self.get(field_name).strip()
                if not re.match(pattern, value):
                    frappe.throw(
                        f"ช่อง {label} สามารถกรอกได้เฉพาะตัวอักษรไทย-อังกฤษเท่านั้น",
                        title="ข้อมูลไม่ถูกต้อง"
                    )
                
                # Check for consecutive spaces or leading/trailing spaces
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
            if self.thai_national_id:  # Changed from national_id to thai_national_id
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
        national_id = self.thai_national_id.replace('-', '').replace(' ', '')  # Changed field name
        
        # Only validate if user seems done entering (has some content)
        # Don't validate if clearly incomplete (less than 10 digits)
        if len(national_id) < 10:
            return
            
        # Check if it's exactly 13 digits
        if not national_id.isdigit() or len(national_id) != 13:
            frappe.throw(
                "เลขบัตรประชาชนต้องเป็นตัวเลข 13 หลักเท่านั้น",
                title="เลขบัตรประชาชนไม่ถูกต้อง"
            )
        
        # Thai National ID checksum validation
        if not self.is_valid_thai_id(national_id):
            frappe.throw(
                "เลขบัตรประชาชนไม่ถูกต้องตามหลักการคำนวณ",
                title="เลขบัตรประชาชนไม่ถูกต้อง"
            )
    
    def is_valid_thai_id(self, national_id):
        """Validate Thai National ID using checksum algorithm"""
        if len(national_id) != 13:
            return False
        
        # Calculate checksum
        sum_value = 0
        for i in range(12):
            sum_value += int(national_id[i]) * (13 - i)
        
        remainder = sum_value % 11
        check_digit = (11 - remainder) % 10
        
        return int(national_id[12]) == check_digit
    
    def validate_passport_number(self):
        """Validate Passport Number - just convert to uppercase, no strict format validation"""
        # Only convert to uppercase, don't restrict format since each country is different
        if self.passport_number:
            self.passport_number = self.passport_number.upper()
    
    def before_save(self):
        """Clean up data before saving"""
        # Clean up name fields (remove extra spaces)
        name_fields = ['first_name', 'middle_name', 'last_name']
        for field in name_fields:
            if self.get(field):
                # Remove extra spaces and convert to proper case
                cleaned_value = ' '.join(self.get(field).split())
                self.set(field, cleaned_value)
        
        # Clean up ID fields
        if self.thai_national_id:  # Changed field name
            self.thai_national_id = self.thai_national_id.replace('-', '').replace(' ', '')
        
        if self.passport_number:
            self.passport_number = self.passport_number.upper().replace(' ', '')
    
    def validate_birth_date(self):
        """Validate birth date is not in the future"""
        if self.birth_date:
            from datetime import date
            from frappe.utils import getdate
            
            today = date.today()
            birth_date = getdate(self.birth_date)  # Convert string to date
            
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
        birth_date = getdate(self.birth_date)  # Convert string to date
        
        if birth_date > today:
            self.age = None
            return
        
        # Calculate age
        age = today.year - birth_date.year
        
        # Adjust if birthday hasn't occurred this year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1
        
        self.age = age

    def validate_visit_dates(self):
        """Validate visit dates"""
        if self.visit_date and self.visit_end_date:
            from frappe.utils import getdate
            
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
                duration = date_diff(end_date, start_date) + 1  # +1 to include both days
                self.total_days = duration
            else:
                self.total_days = None
        else:
            self.total_days = None

    def validate_terms_acceptance(self):
        """Validate that terms are accepted when visitor photo is uploaded"""
        # Only validate if both photo and checkbox field exist
        if hasattr(self, 'visitor_photo') and hasattr(self, 'terms_accepted'):
            if self.visitor_photo and not self.terms_accepted:
                frappe.throw(
                    "กรุณายอมรับเงื่อนไขการเข้า-ออกสถานที่",
                    title="จำเป็นต้องยอมรับเงื่อนไข"
                )

    def before_save(self):
        """Clean up data and generate QR code before saving"""
        # Clean up name fields (remove extra spaces)
        name_fields = ['first_name', 'middle_name', 'last_name']
        for field in name_fields:
            if self.get(field):
                # Remove extra spaces and convert to proper case
                cleaned_value = ' '.join(self.get(field).split())
                self.set(field, cleaned_value)
        
        # Clean up ID fields
        if self.thai_national_id:
            self.thai_national_id = self.thai_national_id.replace('-', '').replace(' ', '')
        
        if self.passport_number:
            self.passport_number = self.passport_number.upper().replace(' ', '')
        
        # Generate QR Code when visitor photo and terms acceptance are complete
        if self.visitor_photo and self.terms_accepted:
            self.generate_qr_code()

    def generate_qr_code(self):
        """Generate QR code with visitor information and validity period"""
        import json
        import qrcode
        import io
        import base64
        from frappe.utils import getdate, now_datetime
        
        if not self.visit_date or not self.visit_end_date:
            return
        
        # Calculate QR code validity period
        start_date = getdate(self.visit_date)
        end_date = getdate(self.visit_end_date)
        
        # Compact QR Code data to reduce size
        qr_data = {
            "id": self.name,
            "name": f"{self.first_name or ''} {self.last_name or ''}".strip(),
            "phone": self.phone_number,
            "purpose": self.purpose,
            "start": str(start_date),
            "end": str(end_date),
            "days": self.total_days,
            "gen": str(now_datetime())[:19],  # Remove microseconds
            "status": "active"
        }
        
        # Convert to compact JSON string
        qr_string = json.dumps(qr_data, ensure_ascii=False, separators=(',', ':'))
        
        try:
            # Generate QR code image
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_string)
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert image to base64 string
            img_buffer = io.BytesIO()
            qr_img.save(img_buffer, format='PNG')
            img_str = base64.b64encode(img_buffer.getvalue()).decode()
            
            # Save as file attachment
            from frappe.utils.file_manager import save_file
            file_doc = save_file(
                fname=f"qr_code_{self.name}.png",
                content=base64.b64decode(img_str),
                dt=self.doctype,
                dn=self.name,
                is_private=1
            )
            
            # Set the QR code field to reference the file
            self.qr_code = file_doc.file_url
            
        except ImportError:
            # Fallback to text if qrcode library not installed
            self.qr_code = qr_string
            frappe.msgprint(
                "QR Code library ไม่พร้อมใช้งาน กรุณาติดตั้ง: pip install qrcode[pil]",
                title="ข้อมูล",
                indicator="orange"
            )
            return
        
        frappe.msgprint(
            f"QR Code สร้างเรียบร้อย ใช้ได้ตั้งแต่ {start_date} ถึง {end_date} ({self.total_days} วัน)",
            title="QR Code พร้อมใช้งาน",
            indicator="green"
        )
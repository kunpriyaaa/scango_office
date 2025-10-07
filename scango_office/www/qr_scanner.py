import frappe
from frappe.utils import getdate, date_diff, now_datetime

def get_context(context):
    """QR Scanner - ตรวจสอบและบันทึก Gate Pass ตาม Machine Gate"""
    context.no_cache = 1
    
    # รับค่า QR ID และ Machine Gate ID
    visitor_id = frappe.form_dict.get('id')
    machine_id = frappe.form_dict.get('machine') or frappe.form_dict.get('name')
    
    if not visitor_id:
        context.error = "ไม่พบข้อมูล QR Code"
        context.error_message = "กรุณาสแกน QR Code ที่ถูกต้อง"
        return context
    
    if not machine_id:
        context.error = "ไม่พบข้อมูลเครื่อง"
        context.error_message = "กรุณาระบุ Machine Gate"
        return context
    
    try:
        # ดึงข้อมูล Machine Gate
        machine = frappe.get_doc("Machine Gate", machine_id)
        
        # เช็คว่าเป็น CheckStatus หรือไม่
        if machine.use_for == "CheckStatus":
            # แสดงข้อมูล QR + บันทึก Gate Pass
            return show_qr_info(context, visitor_id, machine)
        else:
            # บันทึก Gate Pass แบบปกติ (In/Out/Checkout)
            return record_gate_pass(context, visitor_id, machine)
            
    except frappe.DoesNotExistError:
        context.error = "ไม่พบข้อมูลเครื่อง"
        context.error_message = f"ไม่พบ Machine Gate: {machine_id}"
        return context
    except Exception as e:
        frappe.log_error(f"QR Scanner Error: {str(e)}")
        context.error = "เกิดข้อผิดพลาด"
        context.error_message = "กรุณาติดต่อเจ้าหน้าที่"
        return context

def show_qr_info(context, visitor_id, machine):
    """แสดงข้อมูล QR และบันทึก Gate Pass (สำหรับ CheckStatus)"""
    try:
        visitor = frappe.get_doc("Visitor Register", visitor_id)
        
        # คำนวณสถานะ
        today = getdate()
        start_date = getdate(visitor.visit_date)
        end_date = getdate(visitor.visit_end_date)
        
        if today < start_date:
            status = "ยังไม่ถึงวันเข้า"
            status_color = "orange"
            days_left = date_diff(start_date, today)
            days_text = f"อีก {days_left} วัน"
        elif today > end_date:
            status = "หมดอายุแล้ว"
            status_color = "red"
            days_left = 0
            days_text = f"หมดอายุเมื่อ {date_diff(today, end_date)} วันที่แล้ว"
        else:
            status = "ใช้งานได้"
            status_color = "green"
            days_left = date_diff(end_date, today) + 1
            days_text = f"เหลืออีก {days_left} วัน"
        
        # บันทึก Gate Pass
        try:
            # gate_pass = frappe.get_doc({
            #     "doctype": "Visitor Gate Pass",
            #     "visitor_register": visitor_id,
            #     "visitor_name": f"{visitor.first_name} {visitor.last_name or ''}",
            #     "machine_gate": machine.name,
            #     "building_gate": machine.building_gate,
            #     "pass_type": machine.use_for,
            #     "pass_datetime": now_datetime(),
            #     "security_guard": frappe.session.user
            # })
            # gate_pass.insert(ignore_permissions=True)
            # frappe.db.commit()
            
            context.gate_pass_recorded = True
            context.gate_pass_time = gate_pass.pass_datetime.strftime("%d/%m/%Y %H:%M:%S")
        except Exception as e:
            frappe.log_error(f"Gate Pass Recording Error: {str(e)}")
            context.gate_pass_recorded = False
        
        context.mode = "check_status"
        context.visitor = visitor
        context.status = status
        context.status_color = status_color
        context.days_text = days_text
        context.scan_time = now_datetime().strftime("%d/%m/%Y %H:%M:%S")
        context.machine = machine
        
    except frappe.DoesNotExistError:
        context.error = "ไม่พบข้อมูล"
        context.error_message = f"ไม่พบข้อมูลผู้เยี่ยมชม ID: {visitor_id}"
    except Exception as e:
        frappe.log_error(f"Show QR Info Error: {str(e)}")
        context.error = "เกิดข้อผิดพลาด"
        context.error_message = str(e)
    
    return context

def record_gate_pass(context, visitor_id, machine):
    """บันทึก Gate Pass (สำหรับ In/Out/Checkout)"""
    try:
        visitor = frappe.get_doc("Visitor Register", visitor_id)
        
        #สร้าง Gate Pass
        gate_pass = frappe.get_doc({
            "doctype": "Visitor Gate Pass",
            "visitor_register": visitor_id,
            "visitor_name": f"{visitor.first_name} {visitor.last_name or ''}",
            "machine_gate": machine.name,
            "building_gate": machine.building_gate,
            "pass_type": machine.use_for,
            "pass_datetime": now_datetime(),
            "security_guard": frappe.session.user
        })
        gate_pass.insert(ignore_permissions=True)
        frappe.db.commit()
        
        context.mode = "gate_pass"
        context.visitor = visitor
        context.gate_pass = gate_pass
        context.machine = machine
        context.success = True
        
    except frappe.DoesNotExistError:
        context.error = "ไม่พบข้อมูล"
        context.error_message = f"ไม่พบข้อมูลผู้เยี่ยมชม ID: {visitor_id}"
    except Exception as e:
        frappe.log_error(f"Gate Pass Error: {str(e)}")
        context.error = "เกิดข้อผิดพลาด"
        context.error_message = "ไม่สามารถบันทึกข้อมูลได้"
    
    return context
import frappe
from frappe.model.document import Document

class MachineGate(Document):
    
    @frappe.whitelist()
    def processCheckIn(self, qr_content, machine_name):
        # Logic สำหรับ Check In
        return {
            "success": True, 
            "message": "เข้าสำเร็จ"
        }
    
    @frappe.whitelist()
    def processCheckOut(self, qr_content, machine_name):
        # Logic สำหรับ Check Out  
        return {
            "success": True,
            "message": "ออกสำเร็จ"
        }
    
    @frappe.whitelist()
    def processCheckStatus(self, qr_content, machine_name):
        # Logic สำหรับ Check Status
        return {
            "success": True,
            "message": "ตรวจสอบสำเร็จ"
        }
    
    @frappe.whitelist() 
    def processCheckout(self, qr_content, machine_name):
        # Logic สำหรับ Checkout
        return {
            "success": True,
            "message": "ลงเวลาสำเร็จ"
        }
import frappe
import json
from frappe.utils import getdate, now_datetime
from datetime import datetime
from urllib.parse import urlparse, parse_qs, unquote

def get_context(context):
    """Get context for QR scanner page"""
    
    # Get QR Code data from URL parameter
    qr_data = frappe.form_dict.get('data')
    visitor_id = frappe.form_dict.get('id')
    
    # Default context
    context.update({
        'title': 'ระบบสแกน QR Code ผู้เยี่ยมชม (อัตโนมัติ)',
        'visitor_data': None,
        'error_message': None,
        'is_valid': False,
        'access_status': None,
        'available_gates': [],
        'visit_history': [],
        'days_remaining': 0,
        'show_scanner': not (qr_data or visitor_id)
    })
    
    if not qr_data and not visitor_id:
        return context
    
    try:
        visitor_data = None
        
        # กรณีที่ 1: มี qr_data (ข้อมูล JSON หรือ URL)
        if qr_data:
            if qr_data.startswith('http'):
                parsed_url = urlparse(qr_data)
                params = parse_qs(parsed_url.query)
                
                if 'data' in params:
                    json_data = unquote(params['data'][0])
                    visitor_data = json.loads(json_data)
                elif 'id' in params:
                    visitor_id = params['id'][0]
                    visitor_data = get_visitor_data_from_db(visitor_id)
            else:
                visitor_data = json.loads(qr_data)
        
        # กรณีที่ 2: มี visitor_id อย่างเดียว
        elif visitor_id:
            visitor_data = get_visitor_data_from_db(visitor_id)
        
        if not visitor_data:
            context['error_message'] = "ไม่สามารถประมวลผลข้อมูล QR Code ได้"
            context['show_scanner'] = False
            return context
        
        # Validate visitor data structure
        required_fields = ['id', 'name']
        if not all(field in visitor_data for field in required_fields):
            context['error_message'] = "ข้อมูล QR Code ไม่ครบถ้วน"
            context['show_scanner'] = False
            return context
        
        # ตรวจสอบว่ามีในระบบไหม
        try:
            visitor_register = frappe.get_doc('Visitor Register', visitor_data['id'])
        except frappe.DoesNotExistError:
            context['error_message'] = f"ไม่พบข้อมูลผู้เยี่ยมชม ID: {visitor_data['id']}"
            context['show_scanner'] = False
            return context
        
        # ตรวจสอบวันที่
        days_remaining = 0
        if visitor_data.get('start') and visitor_data.get('end'):
            today = getdate()
            start_date = getdate(visitor_data['start'])
            end_date = getdate(visitor_data['end'])
            
            if today < start_date:
                context['error_message'] = f"QR Code ยังไม่สามารถใช้ได้ (เริ่มใช้ได้วันที่ {start_date})"
                context['show_scanner'] = False
                return context
            elif today > end_date:
                context['error_message'] = f"QR Code หมดอายุแล้ว (หมดอายุวันที่ {end_date})"
                context['show_scanner'] = False
                return context
            
            days_remaining = (end_date - today).days + 1
        
        # Get available gates and history
        gates = get_available_gates()
        visit_history = get_visit_history(visitor_data['id'])
        
        context.update({
            'visitor_data': visitor_data,
            'visitor_register': visitor_register,
            'is_valid': True,
            'available_gates': gates,
            'visit_history': visit_history,
            'days_remaining': max(0, days_remaining),
            'is_last_day': days_remaining <= 1,
            'current_date': getdate(),
            'show_scanner': False
        })
        
    except json.JSONDecodeError as e:
        context['error_message'] = "รูปแบบ QR Code ไม่ถูกต้อง"
        context['show_scanner'] = False
    except Exception as e:
        frappe.log_error(f"Error processing QR Code: {str(e)}")
        context['error_message'] = f"เกิดข้อผิดพลาด: {str(e)}"
        context['show_scanner'] = False
    
    return context

def get_visitor_data_from_db(visitor_id):
    """ดึงข้อมูลผู้เยี่ยมชมจาก database"""
    try:
        visitor_register = frappe.get_doc('Visitor Register', visitor_id)
        return {
            "id": visitor_id,
            "name": f"{getattr(visitor_register, 'first_name', '')} {getattr(visitor_register, 'last_name', '')}".strip(),
            "phone": getattr(visitor_register, 'phone_number', ''),
            "purpose": getattr(visitor_register, 'purpose', ''),
            "start": str(getattr(visitor_register, 'visit_date', '')),
            "end": str(getattr(visitor_register, 'visit_end_date', ''))
        }
    except frappe.DoesNotExistError:
        return None

def get_available_gates():
    """Get list of available gates"""
    try:
        gates = frappe.get_all(
            'Building Gate',
            fields=['name', 'gate_name', 'building_name'],
            order_by='building_name, gate_name'
        )
        return gates
    except Exception:
        return []

def get_visit_history(visitor_id, limit=10):
    """Get recent visit history for the visitor"""
    try:
        history = frappe.get_all(
            'Visitor Gate Pass',
            filters={'visitor_register': visitor_id},
            fields=['gate_name', 'building_name', 'entry_type', 'scan_datetime'],
            order_by='scan_datetime desc',
            limit=limit
        )
        return history
    except Exception:
        return []

@frappe.whitelist(allow_guest=True, methods=['POST'])
def record_gate_access(visitor_id, gate_id):
    """API endpoint to record gate access - เก็บประวัติการสแกนทั้งหมด"""
    
    # IMPORTANT: Handle CSRF for guest users
    if frappe.session.user == 'Guest':
        frappe.flags.ignore_csrf = True
    
    try:
        # Parse JSON data from request body if needed
        if frappe.request.data:
            data = json.loads(frappe.request.data)
            visitor_id = data.get('visitor_id', visitor_id)
            gate_id = data.get('gate_id', gate_id)
        
        if not visitor_id or not gate_id:
            frappe.response['http_status_code'] = 400
            return {'success': False, 'message': 'ข้อมูลไม่ครบถ้วน: ต้องมี visitor_id และ gate_id'}
        
        if not frappe.db.exists('Visitor Register', visitor_id):
            frappe.response['http_status_code'] = 404
            return {'success': False, 'message': f'ไม่พบข้อมูลผู้เยี่ยมชม: {visitor_id}'}
        
        if not frappe.db.exists('Building Gate', gate_id):
            frappe.response['http_status_code'] = 404
            return {'success': False, 'message': f'ไม่พบข้อมูลประตู: {gate_id}'}
        
        # ดึงข้อมูล
        gate = frappe.db.get_value('Building Gate', gate_id, ['gate_name', 'building_name'], as_dict=True)
        visitor = frappe.db.get_value('Visitor Register', visitor_id, ['first_name', 'last_name'], as_dict=True)
        
        # ตรวจสอบการเข้าออกล่าสุดของประตูนี้เฉพาะ
        last_entry = frappe.get_all(
            'Visitor Gate Pass',
            filters={
                'visitor_register': visitor_id,
                'building_gate': gate_id
            },
            fields=['entry_type', 'scan_datetime'],
            order_by='scan_datetime desc',
            limit=1
        )
        
        # กำหนดประเภทการเข้า-ออก (สลับกันไปมา)
        entry_type = 'เข้า'
        if last_entry and last_entry[0]['entry_type'] == 'เข้า':
            entry_type = 'ออก'
        
        current_time = now_datetime()
        
        # ดึงประวัติเวลาการสแกนเก่าทั้งหมดของประตูนี้
        existing_scans = frappe.get_all(
            'Visitor Gate Pass',
            filters={
                'visitor_register': visitor_id,
                'building_gate': gate_id
            },
            fields=['scan_datetime', 'entry_type'],
            order_by='scan_datetime asc'
        )
        
        # รวมประวัติเวลาเก่าทั้งหมด + เวลาปัจจุบัน
        all_scan_times = []
        for scan in existing_scans:
            scan_time_str = scan['scan_datetime'].strftime("%d/%m/%Y %H:%M:%S")
            all_scan_times.append(f"{scan['entry_type']}: {scan_time_str}")
        
        # เพิ่มเวลาปัจจุบัน
        current_time_str = current_time.strftime("%d/%m/%Y %H:%M:%S")
        all_scan_times.append(f"{entry_type}: {current_time_str}")
        
        # รวมเป็น string เดียว คั่นด้วย | หรือ line break
        scan_history_text = " | ".join(all_scan_times)
        
        # สร้าง Visitor Gate Pass record ใหม่
        gate_pass = frappe.new_doc('Visitor Gate Pass')
        gate_pass.visitor_register = visitor_id
        gate_pass.first_name = visitor.get('first_name', '')
        gate_pass.last_name = visitor.get('last_name', '')
        gate_pass.building_gate = gate_id
        gate_pass.gate_name = gate.get('gate_name', gate_id)
        gate_pass.building_name = gate.get('building_name', '')
        gate_pass.entry_type = entry_type
        gate_pass.scan_datetime = current_time
        
        # เพิ่ม field สำหรับเก็บประวัติการสแกนทั้งหมด (ถ้ามี)
        if hasattr(gate_pass, 'scan_history'):
            gate_pass.scan_history = scan_history_text
        
        # บันทึกลง database
        gate_pass.insert(ignore_permissions=True)
        frappe.db.commit()
        
        success_response = {
            'success': True,
            'message': f'บันทึกการ{entry_type}ประตู {gate.gate_name} เรียบร้อยแล้ว',
            'entry_type': entry_type,
            'gate_name': gate.get('gate_name', gate_id),
            'building_name': gate.get('building_name', ''),
            'scan_time': current_time_str,
            'scan_history': scan_history_text,
            'total_scans': len(all_scan_times)
        }
        
        frappe.response['http_status_code'] = 200
        return success_response
        
    except json.JSONDecodeError as e:
        error_msg = f"ข้อมูล JSON ไม่ถูกต้อง: {str(e)}"
        frappe.log_error(f"JSON Decode Error: {error_msg}", "QR Scanner API")
        frappe.response['http_status_code'] = 400
        return {'success': False, 'message': error_msg}
        
    except Exception as e:
        error_msg = str(e)
        frappe.log_error(f"Gate Access Error: {error_msg}", "QR Scanner API")
        frappe.response['http_status_code'] = 500
        return {
            'success': False, 
            'message': f'เกิดข้อผิดพลาดภายในระบบ: {error_msg}'
        }
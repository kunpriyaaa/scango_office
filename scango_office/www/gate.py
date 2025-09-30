import frappe

def get_context(context):

    machine_name = frappe.form_dict.get('name')
    context.mechine = None
    try :
        if machine_name :
            context.machine_name  = machine_name
            machine = frappe.get_doc("Machine Gate",machine_name)

            if machine : 
                context.machine = machine
    except Exception as e :
        context.error = str(e)
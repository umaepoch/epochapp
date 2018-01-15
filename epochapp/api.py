from __future__ import unicode_literals
import frappe
from frappe.utils import add_days, cint, cstr, flt, getdate, rounded, date_diff, money_in_words
from frappe.model.naming import make_autoname

from frappe import msgprint, _, throw
#from erpnext.hr.doctype.process_payroll.process_payroll import get_start_end_dates
from erpnext.hr.doctype.employee.employee import get_holiday_list_for_employee
from erpnext.utilities.transaction_base import TransactionBase
from frappe.model.mapper import get_mapped_doc
from erpnext.accounts.party import get_party_account_currency
from frappe.desk.notifications import clear_doctype_notifications

@frappe.whitelist()
def calculate_overtime_and_food(employee, start_date, end_date):
	
	overtime_hours = frappe.db.sql("""select sum(overtime_hours)
			from `tabAttendance` where employee = %s and attendance_date >= %s and attendance_date <= %s""",
			(employee, start_date, end_date))

	food_allow = frappe.db.sql("""select count(food_allowance)
			from `tabAttendance` where employee = %s and attendance_date >= %s and attendance_date <= %s and food_allowance = 'Yes'""", (employee, start_date, end_date))

#	food_allow = food_allow[0][0]
	
	
	return overtime_hours, food_allow

#	overtime_amount = ((emp_basic + emp_da)/30/8 * overtime_hours)



def get_company_currency(company):
        currency = frappe.db.get_value("Company", company, "default_currency", cache=True)
        if not currency:
                currency = frappe.db.get_default("currency")
        if not currency:
                throw(_('Please specify Default Currency in Company Master and Global Defaults'))

        return currency



@frappe.whitelist()
def get_items(doc):
	msgprint(_("Inside api 2"))
#	self.set('items', [])
		
	doc.validate_production_order()

	if not doc.posting_date or not doc.posting_time:
		frappe.throw(_("Posting date and posting time is mandatory"))

	doc.set_production_order_details()

	if doc.bom_no:
		if doc.purpose in ["Material Issue", "Material Transfer", "Manufacture", "Repack",
			"Subcontract", "Material Transfer for Manufacture"]:
			if doc.production_order and doc.purpose == "Material Transfer for Manufacture":
				item_dict = doc.get_pending_raw_materials()
				if doc.to_warehouse and doc.pro_doc:
					for item in item_dict.values():
						item["to_warehouse"] = doc.pro_doc.wip_warehouse
				doc.add_to_stock_entry_detail(item_dict)

			elif doc.production_order and doc.purpose == "Manufacture" and \
				frappe.db.get_single_value("Manufacturing Settings", "backflush_raw_materials_based_on")== "Material Transferred for Manufacture":
				doc.get_transfered_raw_materials()

			else:
				if not doc.fg_completed_qty:
					frappe.throw(_("Manufacturing Quantity is mandatory"))
					item_dict = doc.get_bom_raw_materials(doc.fg_completed_qty)
					for item in item_dict.values():
						if doc.pro_doc:
							item["from_warehouse"] = doc.pro_doc.wip_warehouse

						item["to_warehouse"] = doc.to_warehouse if doc.purpose=="Subcontract" else ""

					doc.add_to_stock_entry_detail(item_dict)

					scrap_item_dict = doc.get_bom_scrap_material(doc.fg_completed_qty)
					for item in scrap_item_dict.values():
						if doc.pro_doc and doc.pro_doc.scrap_warehouse:
							item["to_warehouse"] = doc.pro_doc.scrap_warehouse
					doc.add_to_stock_entry_detail(scrap_item_dict, bom_no=doc.bom_no)

		# fetch the serial_no of the first stock entry for the second stock entry
		if doc.production_order and doc.purpose == "Manufacture":
			doc.set_serial_nos(doc.production_order)

		# add finished goods item
		if doc.purpose in ("Manufacture", "Repack"):
			doc.load_items_from_bom()

	doc.set_actual_qty()
	doc.calculate_rate_and_amount()




def get_tax(purchase_receipt_number,warehouse,item_code):
	        msgprint(_(warehouse))
		msgprint(_(purchase_receipt_number))
		msgprint(_(item_code))
		
                item_tax = flt(frappe.db.sql("""select item_tax
			from `tabStock Ledger Entry`
			where warehouse=%s and item_code=%s and voucher_no=%s""",
			(warehouse, item_code, purchase_receipt_number))[0][0])
                msgprint(_(item_tax))
                actual_qty = flt(frappe.db.sql("""select actual_qty
			from `tabStock Ledger Entry`
			where warehouse=%s and item_code=%s and voucher_no=%s""",
			(warehouse, item_code, purchase_receipt_number))[0][0])
                item_tax = flt(item_tax)/ flt(actual_qty)
	        return item_tax

@frappe.whitelist()
def set_total_in_words(doc, method):
    from frappe.utils import money_in_words
    company_currency = get_company_currency(doc.company)
    
    disable_rounded_total = cint(frappe.db.get_value("Global Defaults", None, "disable_rounded_total"))

    if doc.meta.get_field("base_in_words"):
        doc.base_in_words = money_in_words(disable_rounded_total and
            abs(doc.base_grand_total) or abs(doc.base_rounded_total), company_currency)
    if doc.meta.get_field("in_words"):
        doc.in_words = money_in_words(disable_rounded_total and
            abs(doc.grand_total) or abs(doc.rounded_total), doc.currency)
    if doc.meta.get_field("amount_of_duty_in_words"):
        doc.amount_of_duty_in_words = money_in_words(disable_rounded_total and
            abs(doc.excise_amount) or abs(doc.excise_amount), doc.currency)

@frappe.whitelist()
def get_item_stock(item_code, company):
		
        	item_stock = get_stock(item_code, company)
	        
		return item_stock

def get_stock(item_code, company):

                item_stock = flt(frappe.db.sql("""select sum(actual_qty)
			from `tabStock Ledger Entry`
			where item_code=%s and company = %s""",
			(item_code, company))[0][0])

		stock_recon = flt(frappe.db.sql("""select sum(qty_after_transaction)
			from `tabStock Ledger Entry`
			where item_code=%s and company = %s and voucher_type = 'Stock Reconciliation'""",
			(item_code, company))[0][0])

		tot_stock = item_stock + stock_recon
		
       	        return tot_stock

@frappe.whitelist()
def get_warehouse_stock(item_code, warehouse):
		item_whs_stock = get_whs_stock(item_code, warehouse)
	        
		return item_whs_stock

def get_whs_stock(item_code, warehouse):

                item_whs_stock = flt(frappe.db.sql("""select sum(actual_qty)
			from `tabStock Ledger Entry`
			where item_code=%s and warehouse = %s""",
			(item_code, warehouse))[0][0])

		stock_whs_recon = flt(frappe.db.sql("""select sum(qty_after_transaction)
			from `tabStock Ledger Entry`
			where item_code=%s and warehouse = %s and voucher_type = 'Stock Reconciliation'""",
			(item_code, warehouse))[0][0])

		tot_whs_stock = item_whs_stock + stock_whs_recon
		
       	        return tot_whs_stock

@frappe.whitelist()
def get_item_tax(purchase_receipt_number, warehouse, item_code):
	msgprint("Inside get_item_tax")
  	item_tax = get_tax(purchase_receipt_number, warehouse, item_code)
      
        if purchase_receipt_number:
		return item_tax

@frappe.whitelist()
def get_purchase_receipts(item_code, warehouse):
	msgprint("Inside get_purchase_receipts")
	po_numbers = []
	target_po_no = []
  	po_numbers = frappe.db.sql("""select voucher_no, item_tax from `tabStock Ledger Entry` where voucher_type = 'Purchase Receipt' and item_code = %s and warehouse = %s""", (item_code, warehouse))
      
	msgprint(_(po_numbers))
	
        return po_numbers


@frappe.whitelist()
def make_quotation(source_name, target_doc=None):
	
	def set_missing_values(source, target):
		quotation = frappe.get_doc(target)
		
		company_currency = frappe.db.get_value("Company", quotation.company, "default_currency")
		party_account_currency = get_party_account_currency("Customer", quotation.customer,
			quotation.company) if quotation.customer else company_currency
		
		quotation.currency = party_account_currency or company_currency

		if company_currency == quotation.currency:
			exchange_rate = 1
		else:
			exchange_rate = get_exchange_rate(quotation.currency, company_currency)

		quotation.conversion_rate = exchange_rate
		
		quotation.run_method("set_missing_values")
		quotation.run_method("calculate_taxes_and_totals")
		
	doclist = get_mapped_doc("Item Listing", source_name, {
		"Item Listing": {
			"doctype": "Quotation",
			"field_map": {
				"customer": "quotation_to",
				"name": "enq_no",
			}
		},
		"ItemStock": {
			"doctype": "Quotation Item",
			"field_map": {
				"parent": "prevdoc_docname",
				"parenttype": "prevdoc_doctype",
				"uom": "stock_uom"
			},
			"add_if_empty": True
		}
	}, target_doc, set_missing_values)
	
	return doclist


def set_missing_values(source, target_doc):
	target_doc.run_method("set_missing_values")
	target_doc.run_method("calculate_taxes_and_totals")

def update_item(obj, target, source_parent):
	target.conversion_factor = 1
	target.qty = flt(obj.qty)
	target.stock_qty = target.qty

@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None):
	def postprocess(source, target_doc):
		set_missing_values(source, target_doc)

	doclist = get_mapped_doc("Item Listing", source_name, 	{
		"Item Listing": {
			"doctype": "Purchase Order",
			"validation": {
							
			}
		},
		"ItemStock": {
			"doctype": "Purchase Order Item",
			"field_map": [
				["name", "material_request_item"],
				["parent", "material_request"],
				["uom", "stock_uom"],
				["uom", "uom"]
			],
			"postprocess": update_item
			}
	}, target_doc, postprocess)

	return doclist

@frappe.whitelist()
def make_sales_order(source_name, target_doc=None):
	return _make_sales_order(source_name, target_doc)

def _make_sales_order(source_name, target_doc=None, ignore_permissions=False):
	customer = _make_customer(source_name, ignore_permissions)
	
	def set_missing_values(source, target):

		if customer:
#			target.customer = customer.name
			target.customer_name = customer
		target.ignore_pricing_rule = 1
		target.flags.ignore_permissions = ignore_permissions
		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")

	doclist = get_mapped_doc("Item Listing", source_name, {
			"Item Listing": {
				"doctype": "Sales Order",
				"validation": {
					
				}
			},
			"ItemStock": {
				"doctype": "Sales Order Item",
				"field_map": {
					"parent": "prevdoc_docname"
				}
			},
			"Sales Taxes and Charges": {
				"doctype": "Sales Taxes and Charges",
				"add_if_empty": True
			},
			"Sales Team": {
				"doctype": "Sales Team",
				"add_if_empty": True
			}
		}, target_doc, set_missing_values, ignore_permissions=ignore_permissions)

	# postprocess: fetch shipping address, set missing values

	return doclist

def _make_customer(source_name, ignore_permissions=False):
	itemlist = frappe.db.get_value("Item Listing", source_name, ["customer"])

	if itemlist:
		lead_name = itemlist[0]
		customer_name = frappe.db.get_value("Customer", itemlist)

		if not customer_name:
			from erpnext.crm.doctype.lead.lead import _make_customer
			customer_doclist = _make_customer(lead_name, ignore_permissions=ignore_permissions)
			customer = frappe.get_doc(customer_doclist)
			customer.flags.ignore_permissions = ignore_permissions
			

			try:
				customer.insert()
				return customer
			except frappe.NameError:
				if frappe.defaults.get_global_default('cust_master_name') == "Customer Name":
					customer.run_method("autoname")
					customer.name += "-" + lead_name
					customer.insert()
					return customer
				else:
					raise
			except frappe.MandatoryError:
				frappe.local.message_log = []
				frappe.throw(_("Please create Customer from Lead {0}").format(lead_name))
		else:
			return customer_name

@frappe.whitelist()
def make_delivery_note(source_name, target_doc=None):
	def set_missing_values(source, target):
#		if source.po_no:
#			if target.po_no:
#				target_po_no = target.po_no.split(", ")
#				target_po_no.append(source.po_no)
#				target.po_no = ", ".join(list(set(target_po_no))) if len(target_po_no) > 1 else target_po_no[0]
#			else:
#				target.po_no = source.po_no

		target.ignore_pricing_rule = 1
		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")

	def update_item(source, target, source_parent):
#		target.base_amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.base_rate)
#		target.amount = (flt(source.qty) - flt(source.delivered_qty)) * flt(source.rate)
		target.qty = flt(source.qty)

	target_doc = get_mapped_doc("Item Listing", source_name, {
		"Item Listing": {
			"doctype": "Delivery Note",
			"validation": {
				
			}
		},
		"ItemStock": {
			"doctype": "Delivery Note Item",
			"field_map": {
				"rate": "rate",
				"name": "so_detail",
				"parent": "against_sales_order",
			},
			"postprocess": update_item,
			
		},
		"Sales Taxes and Charges": {
			"doctype": "Sales Taxes and Charges",
			"add_if_empty": True
		},
		"Sales Team": {
			"doctype": "Sales Team",
			"add_if_empty": True
		}
	}, target_doc, set_missing_values)

	return target_doc

@frappe.whitelist()
def make_sales_cycle(source_name, target_doc=None):

	target_doc = get_mapped_doc("Opportunity", source_name, {
		"Opportunity": {
			"doctype": "Sales Cycle",
			"field_map": {
				"name": "reference_name"
			 }
		}
		
	}, target_doc, set_missing_values)

	return target_doc


@frappe.whitelist()
def set_sales_cycle_values(opportunity):

        
	max_closing_date = frappe.db.sql("""select max(closing_date) from `tabSales Cycle` where reference_name=%s""",
				(opportunity))
				
        sc_rec = frappe.db.sql("""select value, closing_date, stage, opportunity_purpose, buying_status, support_needed
		from `tabSales Cycle`
		where reference_name=%s and closing_date = %s""",
		(opportunity, max_closing_date))
        
                
        return sc_rec

@frappe.whitelist()
def get_serial_number(item, second_uom, second_uom_qty):

        
	last_serial_number = frappe.db.sql("""select max(sno) from `tabSerial Number`""")[0][0]
	
	next_serial_number = last_serial_number + 1

	frappe.db.sql("""update `tabSerial Number` set sno = %s, item = %s, second_uom = %s, second_uom_qty = %s""", (next_serial_number, item, second_uom, second_uom_qty))	           
	
        return next_serial_number





from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, cstr, comma_or, getdate
from erpnext.setup.utils import get_company_currency
from frappe import _, throw, msgprint
from frappe.model.mapper import get_mapped_doc
from erpnext.accounts.party import get_party_account_currency

def get_tax(purchase_receipt_number,warehouse,item_code):
	        msgprint(_(warehouse))
		msgprint(_(purchase_receipt_number))
		msgprint(_(item_code))
		
                item_tax = flt(frappe.db.sql("""select item_tax
			from `tabStock Ledger Entry`
			where warehouse=%s and item_code=%s and voucher_no=%s""",
			(warehouse, item_code, purchase_receipt_number)))
                msgprint(_(item_tax))
                actual_qty = flt(frappe.db.sql("""select actual_qty
			from `tabStock Ledger Entry`
			where warehouse=%s and item_code=%s and voucher_no=%s""",
			(warehouse, item_code, purchase_receipt_number)))
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
def get_item_stock(item_code):
        	item_stock = get_stock(item_code)
	        
		return item_stock

def get_stock(item_code):

                item_stock = flt(frappe.db.sql("""select sum(actual_qty)
			from `tabStock Ledger Entry`
			where item_code=%s""",
			(item_code))[0][0])

		stock_recon = flt(frappe.db.sql("""select sum(qty_after_transaction)
			from `tabStock Ledger Entry`
			where item_code=%s and voucher_type = 'Stock Reconciliation'""",
			(item_code))[0][0])

		tot_stock = item_stock + stock_recon
		
       	        return tot_stock

@frappe.whitelist()
def get_item_tax(purchase_receipt_number, warehouse, item_code):
	msgprint("Inside get_item_tax")
  	item_tax = get_tax(purchase_receipt_number, warehouse, item_code)
      
        if purchase_receipt_number:
		return item_tax


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


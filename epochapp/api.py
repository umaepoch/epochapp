from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, cstr, comma_or
from erpnext.setup.utils import get_company_currency
from frappe import _, throw, msgprint

def get_tax(batch_no,warehouse,item_code):
                item_tax = flt(frappe.db.sql("""select item_tax
			from `tabStock Ledger Entry`
			where warehouse=%s and item_code=%s and batch_no=%s""",
			(warehouse, item_code, batch_no))[0][0])

                actual_qty = flt(frappe.db.sql("""select actual_qty
			from `tabStock Ledger Entry`
			where warehouse=%s and item_code=%s and batch_no=%s""",
			(warehouse, item_code, batch_no))[0][0])
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
def get_item_tax(batch_no,warehouse,item_code):
  	item_tax = get_tax(batch_no,warehouse,item_code)
      
        if batch_no:
		return item_tax



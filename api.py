
from __future__ import unicode_literals
import frappe
from frappe.utils import cint, flt, cstr, comma_or
from erpnext.setup.utils import get_company_currency
from frappe import _, throw, msgprint

@frappe.whitelist()
def set_total_in_words(doc, method):
from frappe.utils import money_in_words
	msgprint(_("Inside Total in words"))
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
def update_stock_ledger(doc, method, allow_negative_stock=False, via_landed_cost_voucher=False):
		update_ordered_qty()
                msgprint(_("Inside 1"))
		sl_entries = []
		stock_items = get_stock_items()

		for d in self.get('items'):
			if d.item_code in stock_items and d.warehouse:
				pr_qty = flt(d.qty) * flt(d.conversion_factor)
                                
				if pr_qty:
                                        msgprint(_("Inside 2"))
                                        msgprint(_(d.item_tax_amount))
					sle = self.get_sl_entries(d, {
						"actual_qty": flt(pr_qty),
                                                "item_tax": flt(d.item_tax_amount),
						"serial_no": cstr(d.serial_no).strip()
					})
					if self.is_return:
						original_incoming_rate = frappe.db.get_value("Stock Ledger Entry",
							{"voucher_type": "Purchase Receipt", "voucher_no": self.return_against,
							"item_code": d.item_code}, "incoming_rate")

						sle.update({
							"outgoing_rate": original_incoming_rate
						})
					else:
						val_rate_db_precision = 6 if cint(self.precision("valuation_rate", d)) <= 6 else 9
						incoming_rate = flt(d.valuation_rate, val_rate_db_precision)
						sle.update({
							"incoming_rate": incoming_rate
						})
					sl_entries.append(sle)

				if flt(d.rejected_qty) != 0:
					sl_entries.append(self.get_sl_entries(d, {
						"warehouse": d.rejected_warehouse,
						"actual_qty": flt(d.rejected_qty) * flt(d.conversion_factor),
						"serial_no": cstr(d.rejected_serial_no).strip(),
						"incoming_rate": 0.0
					}))

		self.make_sl_entries_for_supplier_warehouse(sl_entries)
              
		self.make_sl_entries(sl_entries, allow_negative_stock=allow_negative_stock,
			via_landed_cost_voucher=via_landed_cost_voucher)



@frappe.whitelist()
def get_item_tax(batch_no,warehouse,item_code):
        item_tax = get_tax(batch_no,warehouse,item_code)
        msgprint(_(item_tax))
        if batch_no:
		return item_tax

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




def update_ordered_qty(self):
		po_map = {}
		for d in self.get("items"):
			if self.doctype=="Purchase Receipt" \
				and d.purchase_order:
					po_map.setdefault(d.purchase_order, []).append(d.purchase_order_item)

			elif self.doctype=="Purchase Invoice" and d.purchase_order and d.po_detail:
				po_map.setdefault(d.purchase_order, []).append(d.po_detail)

		for po, po_item_rows in po_map.items():
			if po and po_item_rows:
				po_obj = frappe.get_doc("Purchase Order", po)

				if po_obj.status in ["Closed", "Cancelled"]:
					frappe.throw(_("{0} {1} is cancelled or closed").format(_("Purchase Order"), po),
						frappe.InvalidStatusError)

				po_obj.update_ordered_qty(po_item_rows)

def make_sl_entries_for_supplier_warehouse(self, sl_entries):
		if hasattr(self, 'supplied_items'):
			for d in self.get('supplied_items'):
				# negative quantity is passed, as raw material qty has to be decreased
				# when PR is submitted and it has to be increased when PR is cancelled
				sl_entries.append(self.get_sl_entries(d, {
					"item_code": d.rm_item_code,
					"warehouse": self.supplier_warehouse,
					"actual_qty": -1*flt(d.consumed_qty),
                                        "item_tax": d.item_tax_amount
				}))

def make_sl_entries(self, sl_entries, is_amended=None, allow_negative_stock=False,
			via_landed_cost_voucher=False):
		from erpnext.stock.stock_ledger import make_sl_entries
		make_sl_entries(sl_entries, is_amended, allow_negative_stock, via_landed_cost_voucher)


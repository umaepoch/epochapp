from __future__ import unicode_literals
import frappe
from frappe import _, throw, msgprint
from frappe.utils import flt, cint, add_days, cstr
import json
from erpnext.setup.utils import get_company_currency
from erpnext.stock.get_item_details import get_bin_details
from erpnext.stock.utils import get_incoming_rate
from erpnext.accounts.party import get_party_details
from erpnext.stock.get_item_details import get_conversion_factor
from erpnext.controllers.stock_controller import StockController


@frappe.whitelist()
def update_stock_ledger(doc, allow_negative_stock=False, via_landed_cost_voucher=False):
		update_ordered_qty(doc)
                sl_entries = []
		stock_items = get_stock_items(doc)

		for d in doc.get('items'):
			if d.item_code in stock_items and d.warehouse:
                                pr_qty = flt(d.qty) * flt(d.conversion_factor)
                                if pr_qty:
                                        
					sle = get_sl_entries(doc, d, {
						"actual_qty": flt(pr_qty),
                                                "serial_no": cstr(d.serial_no).strip()
					})
					
                                        
					if doc.is_return:
                                                
						original_incoming_rate = frappe.db.get_value("Stock Ledger Entry",
							{"voucher_type": "Purchase Receipt", "voucher_no": d.return_against,
							"item_code": d.item_code}, "incoming_rate")

						sle.update({
							"outgoing_rate": original_incoming_rate
						})
					else:
                                                val_rate_db_precision = 6 if cint(doc.precision("valuation_rate", d)) <= 6 else 9
						incoming_rate = flt(d.valuation_rate, val_rate_db_precision)
						sle.update({
							"incoming_rate": incoming_rate
						})
                                        
					sl_entries.append(sle)
                                      
                                     
				if flt(d.rejected_qty) != 0:
                                     
					sl_entries.append(get_sl_entries(doc, d, {
						"warehouse": d.rejected_warehouse,
						"actual_qty": flt(d.rejected_qty) * flt(d.conversion_factor),
						"serial_no": cstr(d.rejected_serial_no).strip(),
						"incoming_rate": 0.0
					}))

		make_sl_entries_for_supplier_warehouse(doc, sl_entries)
              
		make_sl_entries(doc, sl_entries, allow_negative_stock=allow_negative_stock,
			via_landed_cost_voucher=via_landed_cost_voucher)


def update_ordered_qty(doc):
		po_map = {}
                
		for d in doc.get("items"):
			if doc.doctype=="Purchase Receipt" \
				and d.purchase_order:
					po_map.setdefault(d.purchase_order, []).append(d.purchase_order_item)

			elif doc.doctype=="Purchase Invoice" and d.purchase_order and d.po_detail:
				po_map.setdefault(d.purchase_order, []).append(d.po_detail)

		for po, po_item_rows in po_map.items():
			if po and po_item_rows:
				po_obj = frappe.get_doc("Purchase Order", po)

				if po_obj.status in ["Closed", "Cancelled"]:
					frappe.throw(_("{0} {1} is cancelled or closed").format(_("Purchase Order"), po),
						frappe.InvalidStatusError)

				po_obj.update_ordered_qty(po_item_rows)

def make_sl_entries_for_supplier_warehouse(doc, sl_entries):
               
		if hasattr(doc, 'supplied_items'):
			for d in doc.get('supplied_items'):
				# negative quantity is passed, as raw material qty has to be decreased
				# when PR is submitted and it has to be increased when PR is cancelled
                                
				sl_entries.append(get_sl_entries(doc, d, {
					"item_code": d.rm_item_code,
					"warehouse": doc.supplier_warehouse,
					"actual_qty": -1*flt(d.consumed_qty),
                                        "item_tax": d.item_tax_amount,
					"second_uom": d.second_uom,
					"second_uom_qty": d.second_uom_qty
				}))

def make_sl_entries(doc, sl_entries, is_amended=None, allow_negative_stock=False,
			via_landed_cost_voucher=False):
                
		
		if sl_entries:
			from erpnext.stock.utils import update_bin
		
			cancel = True if sl_entries[0].get("is_cancelled") == "Yes" else False
			if cancel:
				set_as_cancel(sl_entries[0].get('voucher_no'), sl_entries[0].get('voucher_type'))
	
			for sle in sl_entries:
				sle_id = None
                               	if sle.get('is_cancelled') == 'Yes':
        				sle['actual_qty'] = -flt(sle['actual_qty'])
				if sle.get("actual_qty") or sle.get("voucher_type")=="Stock Reconciliation":
		
					sle_id = make_entry(doc, sle, allow_negative_stock, via_landed_cost_voucher)
					
					frappe.db.sql("""update `tabStock Ledger Entry` set item_tax = %s, second_uom = %s, second_uom_qty = %s
				                        where item_code=%s and voucher_no = %s and voucher_detail_no = %s and warehouse = %s""",
						(sle['item_tax'], sle['second_uom'], sle['second_uom_qty'], sle['item_code'], sle['voucher_no'], sle['voucher_detail_no'], sle['warehouse']))
					              
                                        sle.update(sle)
					msgprint(_("After update"))
                                        msgprint(_(sle))
                                     				
				args = sle.copy()
                                
				args.update({
					"sle_id": sle_id,
					"is_amended": is_amended
				})
		
				update_bin(args, allow_negative_stock, via_landed_cost_voucher)
		
			if cancel:
				delete_cancelled_entry(sl_entries[0].get('voucher_type'), sl_entries[0].get('voucher_no'))

def set_as_cancel(voucher_type, voucher_no):
	frappe.db.sql("""update `tabStock Ledger Entry` set is_cancelled='Yes',
		modified=%s, modified_by=%s
		where voucher_no=%s and voucher_type=%s""",
		(now(), frappe.session.user, voucher_type, voucher_no))

def make_entry(doc, sle, allow_negative_stock=False, via_landed_cost_voucher=False):
      	sle.update({"doctype": "Stock Ledger Entry"})
        
   #   	sle1 = frappe.get_doc(sle)
        
  #    	sle.flags.ignore_permissions = 1
	sle.allow_negative_stock=allow_negative_stock
	sle.via_landed_cost_voucher = via_landed_cost_voucher
        
	
 #    	sle.insert()
 	msgprint(_(sle))
#	sle.submit()
	msgprint(_(sle.name))
	return sle.name

def delete_cancelled_entry(voucher_type, voucher_no):
	frappe.db.sql("""delete from `tabStock Ledger Entry`
		where voucher_type=%s and voucher_no=%s""", (voucher_type, voucher_no))


def get_stock_items(doc):
		stock_items = []
		item_codes = list(set(item.item_code for item in doc.get("items")))
                
		if item_codes:
			stock_items = [r[0] for r in frappe.db.sql("""select name
				from `tabItem` where name in (%s) and is_stock_item=1""" % \
				(", ".join((["%s"]*len(item_codes))),), item_codes)]

		return stock_items


def get_sl_entries(doc, d, args):
		from erpnext.accounts.utils import get_fiscal_year
		
               	sl_dict = frappe._dict({
			"item_code": d.get("item_code", None),
			"warehouse": d.get("warehouse", None),
			"posting_date": doc.posting_date,
			"posting_time": doc.posting_time,
			'fiscal_year': get_fiscal_year(doc.posting_date, company=doc.company)[0],
			"voucher_type": doc.doctype,
			"voucher_no": doc.name,
			"voucher_detail_no": d.name,
			"actual_qty": (doc.docstatus==1 and 1 or -1)*flt(d.get("stock_qty")),
			"stock_uom": frappe.db.get_value("Item", args.get("item_code") or d.get("item_code"), "stock_uom"),
			"incoming_rate": 0,
			"company": doc.company,
                        "item_tax": d.get("item_tax_amount"),
			"second_uom": d.get("second_uom"),
			"second_uom_qty": d.get("second_uom_qty"),
			"batch_no": cstr(d.get("batch_no")).strip(),
			"serial_no": d.get("serial_no"),
			"project": d.get("project"),
			"is_cancelled": doc.docstatus==2 and "Yes" or "No"
		})
                msgprint(_(sl_dict))
		sl_dict.update(args)
		return sl_dict


def update_bin(args, allow_negative_stock=False, via_landed_cost_voucher=False):
	is_stock_item = frappe.db.get_value('Item', args.get("item_code"), 'is_stock_item')
	if is_stock_item:
		bin = get_bin(args.get("item_code"), args.get("warehouse"))
		bin.update_stock(args, allow_negative_stock, via_landed_cost_voucher)
		return bin
	else:
		frappe.msgprint(_("Item {0} ignored since it is not a stock item").format(args.get("item_code")))

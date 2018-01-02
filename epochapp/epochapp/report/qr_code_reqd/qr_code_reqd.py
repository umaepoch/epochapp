# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _, msgprint
from datetime import datetime, timedelta
from frappe.utils import flt, getdate, datetime,comma_and
from collections import defaultdict
import frappe
import json
import time
import math
import ast
import os.path
import os
#from flask import Flask, send_from_directory
#@app.route('http://localhost:8000/private/files/qrcode.txt')

def execute(filters=None):
	global summ_data
	global data
	global number_labels
	summ_data = []
        if not filters: filters = {}

        columns = get_columns()
       
        iwb_map = get_item_map(filters)

        data = []
        
	diff_data = 0	

        for (item_code, serial_number) in sorted(iwb_map):
                qty_dict = iwb_map[item_code, serial_number]
                data.append([
                        serial_number, item_code, qty_dict.warehouse, qty_dict.delivery_required_at, qty_dict.delivery_required_on, qty_dict.vehicle_status, qty_dict.creation
                        
                    ])

	number_labels = filters.get("number_labels")
	for rows in data: 

		created_date = getdate(rows[6])
		created_from = getdate(filters.get("created_from"))
		created_to = getdate(filters.get("created_to"))
	
		if ((created_date >= created_from) and (created_date <= created_to)):
#			string_qr = "http://www.barcodes4.me/barcode/qr/myfilename.png?value=" + rows[0]

		
			summ_data.append([rows[0], rows[1],rows[2],
		 	rows[3], rows[4], rows[5], rows[6], number_labels
				
			]) 
						 
	return columns, summ_data 


def get_columns():
        """return columns"""
               
        columns = [
		_("Serial Number")+"::100",
		_("Item Code")+"::100",
		_("Warehouse")+"::100",
		_("Delivery Required At")+"::150",
		_("Delivery Required On")+"::100",
		_("Vehicle Status")+"::100",
		_("Creation Date")+":Date:100",
		_("Number of labels")+"::10"
		
         ]

        return columns

def get_conditions(filters):
        conditions = ""
        if filters.get("created_from"):
		created_date = getdate(filters.get("created_from"))

		conditions += " and sn.creation = '%s'" % frappe.db.escape(filters["created_from"])

	
        return conditions

def get_serial_numbers(filters):
        conditions = get_conditions(filters)
	
        return frappe.db.sql("""select name as serial_number, item_code as item_code, warehouse, delivery_required_at, delivery_required_on, vehicle_status, creation
                from `tabSerial No` sn
                where sn.vehicle_status = "Invoiced but not Received" order by sn.item_code, sn.name""", as_dict=1)


def get_item_map(filters):
        iwb_map = {}
#        from_date = getdate(filters["from_date"])
 #       to_date = getdate(filters["to_date"])
	
        sle = get_serial_numbers(filters)

        for d in sle:
                key = (d.item_code, d.serial_number)
                if key not in iwb_map:
                        iwb_map[key] = frappe._dict({
                                "si_qty": 0.0,
                        })

                qty_dict = iwb_map[(d.item_code, d.serial_number)]

                
                qty_dict.warehouse = d.warehouse
		qty_dict.delivery_required_at = d.delivery_required_at
		qty_dict.delivery_required_on = d.delivery_required_on
		qty_dict.vehicle_status = d.vehicle_status
		qty_dict.creation = d.creation
		
     
        return iwb_map


@frappe.whitelist()
def make_text(args):
	save_path = '/home/uma/files'
	file_name = os.path.join(save_path, "qrcode.txt")
	f= open(file_name,"w+")
	f.write("^XA~TA000~JSN^LT0^MNW^MTT^PON^PMN^LH0,0^JMA")
	f.write("^PR2,2~SD15^JUS^LRN^CI0^XZ")
	f.write("^XA^MMT^PW812^LL0406^LS0")
	for rows in summ_data:	

#		number_labels = int(number_labels)
		nol = int(number_labels) + 1
		for x in xrange(1, nol):
			f.write("^FT250,79^A0R,28,28^FH\^FD%s^FS" % (rows[0]))
			f.write("^FT533,53^A0R,28,28^FH\^FD%s^FS" % (rows[1]))
			f.write("^FT300,301^BQN,2,8^FH\^FDMA1%s^FS" % (rows[0]))
			f.write("^PQ1,0,1,Y^XZ")
	frappe.msgprint(_("Text File created - Please check 35.164.49.160/files/qrcode.txt"))
	f.close()
#	download_text()


@frappe.whitelist()
def download_text():
	
	frappe.msgprint(_("Inside"))
	return send_from_directory('/home/uma/Downloads', 'qrcode.txt', as_attachment=True, mimetype='text/plain')
#	frappe.msgprint(_('Beginning file download with wget module'))
#	url = 'http://localhost:8000/private/files/qrcode.txt'  
#	os.system("wget private/files/qrcode.txt /home/uma/Downloads/qrcode.txt")
#	frappe.msgprint(_('File downloaded'))


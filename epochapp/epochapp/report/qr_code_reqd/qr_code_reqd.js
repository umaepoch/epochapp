// Copyright (c) 2016, Epoch and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["QR Code Reqd"] = {
	"filters": [
		{
			"fieldname":"created_from",
			"label": __("Created Date From"),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname":"created_to",
			"label": __("Created Date To"),
			"fieldtype": "Date",
			"reqd": 1
		},
		{
			"fieldname":"number_labels",
			"label": __("Number of Labels"),
			"fieldtype": "Data",
			"default": 1,
			"reqd": 1
		}
		
	],
     onload: function(report) {
        report.page.add_inner_button(__("Make Text File"),
                function() {
                  var args = "as a draft"
                  var reporter = frappe.query_reports["QR Code Reqd"];
                    reporter.maketextfile(report,args);},'Make Text File')
                    
              },

    isNumeric: function( obj ) {
    return !jQuery.isArray( obj ) && (obj - parseFloat( obj ) + 1) >= 0;
  },
   maketextfile: function(report,status){
    var filters = report.get_values();
     if (filters.created_to) {
         return frappe.call({
             method: "motoinventory_tracker.motoinventory_tracker.report.qr_code_reqd.qr_code_reqd.make_text",
             args: {
                 "args": status
             },
             callback: function(r) {
               if(r.message) {
                 frappe.set_route('List',r.message );
             }
             }
         })
     } else {
         frappe.msgprint("Please select all filters for creating Text File")
     }

   }
}


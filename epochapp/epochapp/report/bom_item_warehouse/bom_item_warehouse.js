// Copyright (c) 2016, Epoch and contributors
// For license information, please see license.txt

frappe.query_reports["BOM Item Warehouse"] = {
		                       
		"filters": [
		 {
                        "fieldname":"bom",
                        "label": __("BOM"),
                        "fieldtype": "Link",
                        "options": "BOM",
			"reqd": 1,
			"get_query": function(){ return {'filters': [['BOM', 'docstatus', '=', '1']]}}
						                        
                },
                
		{
                        "fieldname":"company",
                        "label": __("Company"),
                        "fieldtype": "Link",
                        "options": "Company",
			"reqd": 1
                        
                },
                
                {
                        "fieldname":"warehouse",
                        "label": __("Warehouse"),
                        "fieldtype": "Link",
                        "options": "Warehouse",
			"default": "All Warehouse"
		},
                {
                        "fieldname":"item_code",
                        "label": __("Item"),
                        "fieldtype": "Link",
                        "options": "Item"
                },
                       
		{
			"fieldname":"include_exploded_items",
			"label": __("Include Exploded Items"),
			"fieldtype": "Data",
                        "default": "Y"
			
		},

		{
			"fieldname":"qty_to_make",
			"label": __("Qty to Make"),
			"fieldtype": "Data",
                        "default": "1"
			
		}          

        ],
onload: function(report) {
		report.page.add_inner_button(__("Make Stock Requisition"), function() {
			var filters = report.get_values();
if(filters.company && filters.warehouse && filters.bom){
	return  frappe.call({
		method:"epochapp.epochapp.report.bom_item_warehouse.bom_item_warehouse.make_stock_requisition",
		callback: function(r) {
			if(r.message){
    frappe.set_route('Form', 'Stock Requisition',r.message);
	}
}


	})
}else{
	frappe.msgprint("Please select all three filters For Stock Requisition")
}
	});
	}
}



// $(function() {
//      $(wrapper).bind("show", function() {
//              frappe.query_report.load();
//      });
// });


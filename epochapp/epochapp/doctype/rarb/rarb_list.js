frappe.listview_settings['RARB'] = {
	add_fields: ["active", "is_default"],
	get_indicator: function(doc) {
		if(doc.active) {
			return [__("Active"), "blue", "is_active,=,Yes"];
		} else if(!doc.is_active) {
			return [__("Not active"), "darkgrey", "is_active,=,No"];
		}
	}
};


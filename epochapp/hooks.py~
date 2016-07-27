# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "epochapp"
app_title = "Epochapp"
app_publisher = "Epoch"
app_description = "Epoch App"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "umag"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/epochapp/css/epochapp.css"
# app_include_js = "/assets/epochapp/js/epochapp.js"

# include js, css files in header of web template
# web_include_css = "/assets/epochapp/css/epochapp.css"
# web_include_js = "/assets/epochapp/js/epochapp.js"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "epochapp.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "epochapp.install.before_install"
# after_install = "epochapp.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "epochapp.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

doc_events = {
       "Sales Invoice": {
                "validate": "epochapp.api.set_total_in_words"
             }
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"epochapp.tasks.all"
# 	],
# 	"daily": [
# 		"epochapp.tasks.daily"
# 	],
# 	"hourly": [
# 		"epochapp.tasks.hourly"
# 	],
# 	"weekly": [
# 		"epochapp.tasks.weekly"
# 	]
# 	"monthly": [
# 		"epochapp.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "epochapp.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "epochapp.event.get_events"
# }


# Copyright (c) 2024, CloudGCS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _


class ServiceExtensionType(Document):
	def validate(self):
		self.check_for_underscore("Name", self.name)

	def before_rename(self, old_name, new_name, merge=False):
		self.check_for_underscore("Name", new_name)
	
	def check_for_underscore(self, field_name, value):
		if "_" in value:
			frappe.throw(_(f"{field_name} cannot contain underscore for doc: {self.name}"))

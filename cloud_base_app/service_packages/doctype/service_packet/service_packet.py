# Copyright (c) 2024, CloudGCS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class ServicePacket(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		code_name: DF.Data
		description: DF.Text | None
		is_system_packet: DF.Check
		release_version: DF.Link | None
		service_provider: DF.Link
		title: DF.Data
	# end: auto-generated types

	def validate(self):
		self.check_for_underscore("Packet Code", self.code_name)

	def check_for_underscore(self, field_name, value):
		if "_" in value:
			frappe.throw(_(f"{field_name} cannot contain underscore for doc: {self.name}"))

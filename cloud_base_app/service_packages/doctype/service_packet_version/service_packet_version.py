# Copyright (c) 2024, CloudGCS and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ServicePacketVersion(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from cloud_base_app.service_packages.doctype.service_packet_extension.service_packet_extension import ServicePacketExtension
		from frappe.types import DF

		extensions: DF.TableMultiSelect[ServicePacketExtension]
		major: DF.Int
		minor: DF.Int
		service_packet: DF.Link
		version: DF.Data | None
	# end: auto-generated types

	pass

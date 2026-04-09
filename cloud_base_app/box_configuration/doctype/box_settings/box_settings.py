# Copyright (c) 2024, CloudGCS and contributors
# For license information, please see license.txt

import requests
import frappe
from frappe.frappeclient import FrappeClient
from frappe.model.document import Document


class BoxSettings(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		box_type: DF.Literal["Service Box", "Client Box"]
		box_uri: DF.Data | None
		emqx_hostname: DF.Data | None
		warehouse_api_key: DF.Data | None
		warehouse_secret_key: DF.Password | None
		warehouse_url: DF.Data | None
	# end: auto-generated types

 
	def before_insert(self):
		self.check_url()

	def check_url(self):
		if self.warehouse_url:
			valid_url_schemes = ("http", "https")
			try:
				frappe.utils.validate_url(self.warehouse_url, throw=True, valid_schemes=valid_url_schemes)
			except frappe.ValidationError:
				self.warehouse_url = None
				return

			# remove '/' from the end of the url like http://test_site.com/
			# to prevent mismatch in get_url() results
			if self.warehouse_url.endswith("/"):
				self.warehouse_url = self.warehouse_url[:-1]


def get_warehouse_client():
	box = frappe.get_single("Box Settings")
	if box.warehouse_url and box.warehouse_api_key and box.get_password("warehouse_secret_key"):
		warehouse_site = FrappeClient(url=box.warehouse_url, api_key=box.warehouse_api_key, api_secret=box.get_password("warehouse_secret_key"))
		return warehouse_site
	return None

def check_packets_update():
	tenant_code = frappe.get_single("Tenant Settings").tenant_code
	warehouse_site = get_warehouse_client()
	if not warehouse_site:
		return None
	try:
		response = warehouse_site.post_api(
			"service_warehouse.release_service.check_update",
			params={"tenant_code": tenant_code},
		)
	except Exception as e:
		print(f"An error occurred: {e}")
		return None
	if response:
		return response
	# No response from the warehouse site
	return None

def get_packet_from_warehouse(packet_release_version):
	warehouse_site = get_warehouse_client()
	response = warehouse_site.post_api(
		"service_warehouse.release_service.get_service_package",
		params={"packet_release_version": packet_release_version},
	)
	if response:
		return response
	frappe.throw("No response from the warehouse site")

def get_extension_file_from_warehouse(file_path):
	box = frappe.get_single("Box Settings")
	file_url = box.warehouse_url + file_path
	response = requests.get(file_url, auth=(box.warehouse_api_key, box.get_password("warehouse_secret_key")))
	if response.status_code == 200:
		return response.content
	
	frappe.throw("No response from the warehouse site")	

def get_box_uri():
	box = frappe.get_single("Box Settings")
	if box.box_uri:
		return box.box_uri
	return None

def get_emqx_hostname():
	box = frappe.get_single("Box Settings")
	if box.emqx_hostname:
		return box.emqx_hostname
	return None	
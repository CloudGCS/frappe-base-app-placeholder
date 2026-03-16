# Copyright (c) 2024, CloudGCS and contributors
# For license information, please see license.txt

# import frappe
import json
import frappe
import requests


from frappe.frappeclient import FrappeClient
from frappe.model.document import Document
from frappe import _
from frappe.utils.file_manager import get_file


class ServiceExtension(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		config: DF.JSON | None
		description: DF.Text | None
		extension_code: DF.Data
		extension_type: DF.Link
		file: DF.Attach | None
		is_background_plugin: DF.Check
		library_name: DF.Data | None
		major: DF.Int
		minor: DF.Int
		service_provider: DF.Link
		title: DF.Data
		version: DF.Data | None
	# end: auto-generated types

	def validate(self):
		self.check_for_underscore("Extension Code", self.extension_code)

	# we should not check for underscore in the name field
	# def before_rename(self, old_name, new_name, merge=False):
	# 	self.check_for_underscore("Name", new_name)

	def check_for_underscore(self, field_name, value):
		if "_" in value:
			frappe.throw(_(f"{field_name} cannot contain underscore for doc: {self.name}"))
	
	def before_insert(self):
		if not self.is_version_valid():
			frappe.throw("Your version number should progress, can not be downgrading from the latest version created.")

	def is_version_valid(self):
		# self has major and minor version first retrive all the versions with same library name
		versions = frappe.get_all("Service Extension", 
														filters={"service_provider": self.service_provider, "extension_code": self.extension_code, "extension_type": self.extension_type}, 
														fields=["major", "minor"])

		if not versions:
			return True
		# check if the version is greater
		for version in versions:
			if version.major > self.major:
				return False
			elif version.major == self.major and version.minor >= self.minor:
				return False
		return True



mock_plugin_response = {
  "config": "\"{\\\"isUseMenu\\\":false}\"",
	"file": "private/files/_prod-workdiary-be_logs.txt.zip",
  "description": "v013",
  "libraryName": "banana", # this is the display name
  "name": "banana",
  "version": "0.1.3", # this is the version
  "isBackgroundPlugin": False, 
  "isSystemPlugin": False,
  "id": 90
}

@frappe.whitelist()
def get_pilot_station_plugin(plugin_name: str):
	# check if the document exists
	if not frappe.db.exists("Service Extension", plugin_name):
		frappe.throw("The plugin does not exist")
	
	# todo: check if the plugin is subscribed? (maybe we do not need this)

	extension_doc = frappe.get_doc("Service Extension", plugin_name)
	# create a respopnse from extension doc whose fields match with the mock_plugin_response
	response = {
		"config": extension_doc.config,
		"file": extension_doc.file,
		"description": extension_doc.description,
		"libraryName": extension_doc.display_name,
		"name": extension_doc.library_name,
		"version": extension_doc.version,
		"isBackgroundPlugin": extension_doc.is_background_plugin,
		"isSystemPlugin": extension_doc.is_system_plugin,
		"id": extension_doc.name
	}
	return response

# this is a example of how to upload a file to the server
@frappe.whitelist()
def upload_file(*args,**kwargs):
	service_extension = json.loads(kwargs.get('doc'))
	server = frappe.get_doc("Box Settings")  
	file_url = server.warehouse_url + "private/files/" + "_prod-workdiary-be_logs.txt.zip" # service_extension.get("file")
	
	response = requests.get(file_url, auth=(server.warehouse_api_key, server.get_password("warehouse_secret_key")))
	# Get the service_extension document
	doc = frappe.get_doc("Service Extension", service_extension['name'])
	
	if response.status_code == 200:
		file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": "response.zip",
            "attached_to_doctype": "Service Extension",
            "attached_to_name": doc.name,
						"attached_to_field": "file",
						"is_private": 1,
            "content": response.content
        })
		# Insert the new File document
		file_doc.insert()
		doc.file = "/private/files/response.zip"
		# Save the changes to the document
		doc.save()



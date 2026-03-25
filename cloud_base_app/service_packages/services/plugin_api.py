from collections import namedtuple
import json
import random
import string
from cloud_base_app.box_configuration.doctype.box_settings.box_settings import get_box_uri, get_emqx_hostname
import frappe

from frappe import _
from frappe.utils.file_manager import get_file

import paho.mqtt.publish as publish


PluginInfo = namedtuple('PluginInfo', 
                    [
                      'name', 'description', 'libraryName', 'dllFileUrl', 'jsFileUrl', 'version', 'isBackgroundPlugin'
                    ])

PluginData = namedtuple('PluginData', 
                    [
                      'id', 'name', 'config', 'description', 'libraryName', 'status', 'jsFileUrl', 'version', 'isBackgroundPlugin', 'isSystemPlugin', 'publisherOrganization'
                    ])

# this is called by the pilot station to get the plugin data
@frappe.whitelist()
def get_plugin_data():
	# Extract the doc_name from the request URL
	request_path = frappe.request.path
	base_path = "/api/method/cloud_base_app.service_packages.services.plugin_api.get_plugin_data" 
	doc_name = request_path[len(base_path):].strip("/")

	# Ensure doc_name is provided
	if not doc_name:
			return frappe.local.response.update({
					"http_status_code": 404,
					"message": _("Document name not provided.")
			})

	# Fetch the Service Extension document
	doc = frappe.get_doc("Service Extension", doc_name)
	
	if not doc:
			return frappe.local.response.update({
					"http_status_code": 404,
					"message": _("Document not found.")
			})
	box_uri = get_box_uri()
	if not box_uri:
		# todo: let user know about it...
		return frappe.local.response.update({
					"http_status_code": 404,
					"message": _("Box URI not found.")
			})
	download_url_base = f"{box_uri}/api/method/cloud_base_app.service_packages.services.plugin_api.download_plugin_file/"
	file_url = f"{download_url_base}{doc.name.replace(' ', '%20')}"	
	# Create a PluginData object from the Service Extension document
	plugin_data = PluginData(
			id=doc.name,
			name=doc.library_name,
			config=doc.config,
			description=doc.description,
			libraryName=doc.title,
			status=2,
			jsFileUrl=file_url if doc.extension_type == "PS Plugin"  else None,
			version=f"{doc.major}.{doc.minor}",
			isBackgroundPlugin=doc.is_background_plugin,
			isSystemPlugin=False,
			publisherOrganization="Frappe"
	)

	return plugin_data._asdict()

# this is guest-allowed whitelisted method to let download plugins, used by Mission Controller and Pilot Station
# todo: shall be secured later
@frappe.whitelist(allow_guest=True)
def download_plugin_file():
	# Extract the doc_name from the request URL
	request_path = frappe.request.path
	base_path = "/api/method/cloud_base_app.service_packages.services.plugin_api.download_plugin_file" 
	doc_name = request_path[len(base_path):].strip("/")


	# Ensure doc_name is provided
	if not doc_name:
			return frappe.local.response.update({
					"http_status_code": 404,
					"message": _("Document name not provided.")
			})

	# Fetch the Service Extension document
	doc = frappe.get_doc("Service Extension", doc_name)
	
	if not doc.file:
			return frappe.local.response.update({
					"http_status_code": 404,
					"message": _("No file attached to the document.")
			})
	
	# Extract the file name from the file URL
	file_name = doc.file.split('/')[-1]
	
	# Retrieve the file content using Frappe's file manager
	file_path, file_content = get_file(file_name)
	
	if not file_content:
			return frappe.local.response.update({
					"http_status_code": 404,
					"message": _("Failed to retrieve the file content.")
			})
	
	# Set up the HTTP response to return the ZIP file
	frappe.local.response.filename = file_name
	frappe.local.response.filecontent = file_content
	frappe.local.response.type = "download"


@frappe.whitelist(allow_guest=True)
def publish_aircraft_plugins(aircraft_name, plugins: list[PluginInfo]):
	emqx_host = get_emqx_hostname()
	if not emqx_host:
		# todo: let user know about it...
		frappe.throw('EMQX host name not set yet')
		# print('EMQX host name not set yet')
		return

	tenant_code = frappe.get_value("Tenant Settings", "Tenant Settings", "tenant_code")
	topic = f"{tenant_code}/C/{aircraft_name}/PL"
	message = json.dumps({
    "plugins": [dict(
											name=plugin.name,
											description=plugin.description, 
                      libraryName=plugin.libraryName, 
										 	dllFileUrl=plugin.dllFileUrl, 
                     	jsFileUrl=plugin.jsFileUrl, 
                     	version=plugin.version, 
                     	isBackgroundPlugin=plugin.isBackgroundPlugin
                     ) for plugin in plugins],
				"topicName": "PluginList",
				"version": "1.0.0"
		}, default=lambda o: o.__dict__, ensure_ascii=False)
	

	# random 6 letter string, 3 of them of them uppercase, 3 lowercase and in some random order, prepended with 'frappe-'
	client_id = 'frappe-' + ''.join(random.sample(string.ascii_letters, 6))
	# 

	try:
		publish.single(topic, payload=message, hostname=emqx_host, retain=True, qos=1, client_id=client_id, auth={'username': 'emqx-frappe', 'password': 'public'})
	except Exception as e:
		# todo: log the error - but ignore for now.
		frappe.throw(f"An error occurred: {e}. Please check the hostname set correctly")

# {
#   "topicName": "PluginList",
#   "version": "1.0.0",
#   "plugins": [
#     {
#       "description": "mission-api-plugin", (description)
#       "dllFileUrl": null,
#       "jsFileUrl": "https://gcs-development-images.s3.eu-west-1.amazonaws.com/7c03eef8-f717-42c7-b6fa-38536e8094db.js",
#       "libraryName": "Mission API Plugin",   (title)
#       "name": "mission-api-plugin",          (library_name)
#       "version": "0.7.16-development",        (version)
#       "isBackgroundPlugin": true
#     }
#   ]
# }


# from pilot station to load plugin - 
# backoffice response
#  "result": {
#         "config": "{\"isUseMenu\":true}",
#         "description": "aircraft-switcher v0225",
#         "dllFileUrl": null,
#         "jsFileUrl": "https://gcs-development-images.s3.eu-west-1.amazonaws.com/63b740b5-b97f-410a-b705-4ed0388d73f4.js",
#         "libraryName": "Aircraft Switcher",
#         "name": "aircraft-switcher",
#         "status": 2,
#         "version": "0.2.25-development",
#         "isBackgroundPlugin": true,
#         "isSystemPlugin": true,
#         "publisherUser": null,
#         "aircraftTypes": null,
#         "subscriberCount": 0,
#         "aircraftCount": 0,
#         "simulatorAircraftCount": 0,
#         "isSubscribed": false,
#         "id": 1169
#     },
# expected dto in pilot station
# export interface PluginOutputDto {
#   id: number;
#   config: string;
#   description: string | null;
#   jsFileUrl: string;
#   libraryName: string;
#   name: string;
#   status: PluginStatus;
#   version: string;
#   isBackgroundPlugin: boolean;
#   isSystemPlugin: boolean;
#   publisherOrganization: string | undefined;
# }

# export enum PluginStatus {
#   Unpublished = 1,
#   Published,
#   Hidden,
# }

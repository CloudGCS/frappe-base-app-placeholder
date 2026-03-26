# Copyright (c) 2024, CloudGCS and contributors
# For license information, please see license.txt

import json
import os
import subprocess
import zipfile
import shutil
import requests
import frappe
from frappe.model.document import Document

from cloud_base_app.box_configuration.doctype.box_settings.box_settings import check_packets_update, get_extension_file_from_warehouse, get_packet_from_warehouse
from cloud_base_app.service_packages.mock_warehouse import mock_api, mock_install_api
from cloud_base_app.service_packages.models import ExtensionDto, PacketDto, ServicePacketDto
from frappe.utils.background_jobs import get_jobs


class PacketManager(Document):
    # begin: auto-generated types
    # This code is auto-generated. Do not modify anything in this block.

    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from frappe.types import DF


    # end: auto-generated types

    pass


def fetch_packets_from_warehouse(packets):
  # available_packets = mock_api()
  # available_packets = json.loads(available_packets)
  available_packets = check_packets_update()
  if available_packets is None:
      return None
  # parse and return as Packet model
  return [PacketDto.from_dict(packet) for packet in available_packets]


@frappe.whitelist()
def get_all_packets():
  service_packets = frappe.get_all("Service Packet", fields=['name', 'title', 'release_version', 'service_provider'])
  installed_packets = []
  filtered_packets = []
  for packet in service_packets:
    packet = PacketDto.from_dict(packet)
    packet.installed = True
    installed_packets.append(packet)
  # fetch all available packets from the warehouse
  available_packets = fetch_packets_from_warehouse(installed_packets)
  if available_packets:
    # filter out the installed packets from the available packets
    for packet in available_packets:
      is_installed = False
      for installed_packet in installed_packets:
        if packet.name == installed_packet.name and packet.release_version == installed_packet.release_version:
          is_installed = True
          break
      if not is_installed:
        filtered_packets.append(packet)

  # if the warehouse is offline, return the installed packets only
  response = {
    'is_offline': available_packets is None,
    'packets': [packet.to_dict() for packet in installed_packets + filtered_packets]
  }
  # combine the installed and available packets
  return response

def create_extension_types(list_of_extension_types):
  for extension_type in list_of_extension_types:
      if frappe.db.exists("Service Extension Type", extension_type.name):
          continue
      extension_type_doc = frappe.new_doc("Service Extension Type")
      extension_type_doc.name = extension_type.name
      extension_type_doc.title = extension_type.title
      extension_type_doc.insert()
  return True


def create_service_provider(provider):
  # check if the service provider exists with name
  if frappe.db.exists("Service Provider", provider.name):
      service_provider = frappe.get_doc("Service Provider", provider.name)
      service_provider.title = provider.title
      service_provider.save()
      return True
  service_provider = frappe.new_doc("Service Provider")
  service_provider.name = provider.name
  service_provider.title = provider.title
  service_provider.insert()
  return True


def create_or_get_service_packet(packet: ServicePacketDto):
  # check if the packet exists whose code_name matches with packet.code_name
  if frappe.db.exists("Service Packet", packet.construct_name()):
    return frappe.get_doc("Service Packet", packet.construct_name())

  service_packet = frappe.new_doc("Service Packet")
  service_packet.code_name = packet.code_name
  service_packet.title = packet.title
  service_packet.service_provider = packet.service_provider
  service_packet.is_system_packet = packet.is_system_packet
  service_packet.description = packet.description
  service_packet.insert()
  return service_packet

# todo: same name issue
def attach_file(extension_name, file_path):
  file_content = get_extension_file_from_warehouse(file_path)
  file_doc = frappe.get_doc({
    "doctype": "File",
    "file_name": file_path.split("/")[-1],
    "attached_to_doctype": "Service Extension",
    "attached_to_name": extension_name,
    "attached_to_field": "file",
    "is_private": 1,
    "content": file_content
  })
  # Insert the new File document
  file_doc.insert()

def create_or_get_extensions(list_of_extensions: list[ExtensionDto]):
  service_extensions = []
  for extension in list_of_extensions:
    extension_name = extension.construct_name()
    if frappe.db.exists("Service Extension", extension_name):
      service_extensions.append(frappe.get_doc("Service Extension", extension_name))
      continue
    extension_doc = frappe.new_doc("Service Extension")
    extension_doc.extension_code = extension.extension_code
    extension_doc.title = extension.title
    extension_doc.service_provider = extension.service_provider.name
    extension_doc.extension_type = extension.extension_type.name
    extension_doc.major = extension.major
    extension_doc.minor = extension.minor
    extension_doc.library_name = extension.library_name
    extension_doc.is_background_plugin = extension.is_background_plugin
    extension_doc.file = extension.file
    extension_doc.config = json.dumps(extension.config, indent=2)
    extension_doc.insert()
    if extension.file:
      attach_file(extension_doc.name, extension.file)
    service_extensions.append(extension_doc)
  return service_extensions


def create_packet_version(service_packet_doc, service_extensions: list, packet_dto: ServicePacketDto):
  if frappe.db.exists("Service Packet Version", packet_dto.construct_packet_version_name()):
      frappe.throw("Packet Version already exists - you can not create a duplicate version of the packet")

  # create Service Packet Version
  packet_version = frappe.new_doc("Service Packet Version")
  packet_version.service_packet = service_packet_doc.name
  packet_version.major = packet_dto.major
  packet_version.minor = packet_dto.minor
  packet_version.insert(ignore_mandatory=True)

  # create Service Packet Extension child table
  packet_extensions = []
  for service_extension in service_extensions:
    packet_extension_doc = frappe.new_doc("Service Packet Extension")
    packet_extension_doc.parent = packet_version.name
    packet_extension_doc.parenttype = "Service Packet Version"
    packet_extension_doc.parentfield = "extensions"
    packet_extension_doc.service_extension = service_extension.name
    packet_extension_doc.insert()
    packet_extensions.append(packet_extension_doc)

  packet_version.set("extensions", packet_extensions)
  packet_version.save()
  return packet_version

@frappe.whitelist()
def install_packet(packet_name, release_version, action):
  try:
    # print('This is new version')
    # fetch the packet
    # packet_response = mock_install_api(packet_name, release_version)
    # packet_dto = ServicePacketDto(**json.loads(packet_response))
    packet_from_warehouse = get_packet_from_warehouse(release_version)
    packet_dto = ServicePacketDto(**packet_from_warehouse)
    create_service_provider(packet_dto.service_provider)
    create_extension_types(packet_dto.get_distinct_extension_types())
    service_packet_doc = create_or_get_service_packet(packet_dto)
    service_extensions = create_or_get_extensions(packet_dto.extensions)
    packet_version_doc = create_packet_version(service_packet_doc, service_extensions, packet_dto)
    service_packet_doc.release_version = packet_version_doc.name
    service_packet_doc.save()
    # todo: you may revisit this part
    # if action == "UPDATE":

    jobs = get_jobs()

    any_app_update = update_web_applications(packet_dto)
    # todo: a better response to UI
    if any_app_update:
      enqueued_method = "cloud_base_app.setup.migrate_and_clear_site"
      if not jobs or enqueued_method not in jobs[frappe.local.site]:
        frappe.enqueue(enqueued_method, queue="default", enqueue_after_commit=True)

    return "success"
  except Exception as e:
    frappe.msgprint(f"Error while installing packet")
    return "failed"

def update_web_applications(packet_dto):
  print('Hello World')
  current_path = subprocess.run(["pwd"], stdout=subprocess.PIPE, text=True)
  print(current_path)
  whoami = subprocess.run(["whoami"], stdout=subprocess.PIPE, text=True)
  print(whoami.stdout)

  applications = packet_dto.get_web_applications()
  any_app_update = False
  for application in applications:
    app_name = application.library_name

    # check if an app is installed with the app_name
    installed_apps = frappe.get_installed_apps()
    if app_name not in installed_apps:
      # todo: we have to install the app - this is to do.
      frappe.throw(f"App '{app_name}' is not installed. Not supported at the moment")
      continue

    # a build-in application is only the first version of the app - so ignore.
    if application.is_build_in:
      continue

    file_path = application.file
    file_name = file_path.split("/")[-1]
    # get the file content from its path that is located in the current site
    file_content = frappe.utils.file_manager.get_file(file_name)[1]

    # Run 'pwd' command to get the current working directory
    current_path = os.getcwd()
    print(current_path)

    # Construct the path to the 'temp' directory under the current working directory
    temp_dir = os.path.join(current_path, 'temp')
    file_path = os.path.join(temp_dir, file_name)
    app_temp_path = os.path.join(temp_dir, app_name)

    if os.path.exists(app_temp_path):
      shutil.rmtree(app_temp_path)

    if os.path.exists(file_path):
      os.remove(file_path)

    # Ensure the 'temp' directory exists
    os.makedirs(temp_dir, exist_ok=True)

    # file_content is a zip file, copy it to the temp folder
    with open(file_path, "wb") as fileobj:
      fileobj.write(file_content)

    # Unzip the file using Python's zipfile module
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
      zip_ref.extractall(os.path.join(temp_dir, app_name))

    bench_path = os.path.dirname(current_path)  # This will give <path>
    apps_path = os.path.join(bench_path, 'apps')  # This will give <path>/apps
    # Delete the old app directory
    old_app_path = os.path.join(apps_path, app_name)
    print("Old app path:", old_app_path)
    if os.path.exists(old_app_path):
      shutil.rmtree(old_app_path)

    # Copy the new app directory to the 'apps' directory
    new_app_path = os.path.join(temp_dir, app_name)
    print("New app path:", new_app_path)
    shutil.copytree(new_app_path, old_app_path)
    any_app_update = True

    # delete the temp files
    if os.path.exists(file_path):
      os.remove(file_path)
    if os.path.exists(new_app_path):
      shutil.rmtree(new_app_path)

  return any_app_update



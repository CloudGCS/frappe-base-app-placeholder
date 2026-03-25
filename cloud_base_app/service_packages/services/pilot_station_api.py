import json
import frappe

mock_config = {
  "config": "\"{\\\"isUseMenu\\\":false}\"",
  "description": "v013",
  "libraryName": "banana", # this is the display name
  "name": "banana",
  "version": "0.1.3", # this is the version
  "isBackgroundPlugin": False,
  "isSystemPlugin": False,
  "id": 90
}

@frappe.whitelist()
def get_subscribed_plugins():
  # packets = frappe.get_all("Service Packet", filters={"release_version": ["!=", ""]})
  # extensions = []
  # for packet in packets:
  #   version = frappe.get_doc("Service Packet Version", packet.release_version)
  extensions = []
  plugins = frappe.get_all("Service Extension", filters={"extension_type": 'PS Plugin'}, fields=["*"])
  for plugin in plugins:
    extensions.append({
      "config": json.dumps(json.loads(plugin.config)) if plugin.config else "{}",
      "description": plugin.title,
      "libraryName": plugin.title,
      "name": plugin.library_name,
      "version": f"{plugin.major}.{plugin.minor}", # todo: set it correctly
      "isBackgroundPlugin": True if plugin.is_background_plugin == 1 else False,
      "status": 2, # todo: set random value for now,
      # set random value for now,
      "isSystemPlugin": False,
      "id": plugin.name
    })

  return extensions


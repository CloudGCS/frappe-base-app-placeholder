import json
import frappe


@frappe.whitelist(allow_guest=True)
def get_installed_packet_list():
    packets = frappe.get_all(
        "Service Packet",
        filters={"release_version": ["!=", ""]},
        fields=["name", "title", "description", "release_version"]
    )

    packet_list = []
    for packet in packets:
        packet_list.append({
            "name": packet.name,
            "title": packet.title,
            "description": packet.description,
            "release_version": packet.release_version
        })

    return {
        "status": "success",
        "data": packet_list,
    }
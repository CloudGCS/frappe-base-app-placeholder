// Copyright (c) 2024, CloudGCS and contributors
// For license information, please see license.txt

frappe.ui.form.on("Packet Manager", {
  refresh: (frm) => {
    frappe.call({
      method:
        "cloud_base_app.service_packages.doctype.packet_manager.packet_manager.get_all_packets",
      args: {},
      freeze: true,
      callback: (r) => {
        is_offline = r.message.is_offline || false;
        if (is_offline) {
          frm.set_df_property("warning", "hidden", false);
        }
        build_table(frm, r.message.packets);
      },
      error: (r) => {
        frappe.msgprint(
          "Something went wrong, please try again later\n" + r.message
        );
      },
    });
  },
});

function build_table(frm, packets) {
  cur_frm.handleInstall = function (packet_name, release_version, action) {
    frappe.call({
      method:
        "cloud_base_app.service_packages.doctype.packet_manager.packet_manager.install_packet",
      args: { packet_name, release_version, action },
      freeze: true,
      callback: (r) => {
        if (r.message === "success") {
          frappe.msgprint("Installation successful");
          frm.refresh();
        } else {
          frappe.msgprint("Installation failed\n" + r.message);
        }
      },
      error: (r) => {
        frappe.msgprint(
          "Something went wrong, please try again later\n" + r.message
        );
      },
    });
  };

  let htmlContent = `
    <script>
      function handleInstall(plugin_name, release_version, action) {
        cur_frm.handleInstall(plugin_name, release_version, action)
      }
    </script>
    <style>
      /* Table container with top corners rounded only */
      .packet-table-wrapper {
        overflow: hidden;
        border-radius: 14px 14px 0 0; /* top-left & top-right rounded */
        margin: 12px 0; /* vertical spacing */
        border: none;   /* remove outer border */
      }

      table.packet-table {
        border-collapse: collapse;
        width: 100%;
        white-space: nowrap;
        margin: 0;
      }

      /* Header row: only bottom border and column separators */
      table.packet-table thead th {
        background-color: #f2f2f2;
        font-weight: bold;
        padding: 6px;
        text-align: left;

        border-top: none;           /* no top border */
        border-left: none;          /* no left border */
        border-right: 1px solid #cfcfcf; /* vertical separator */
        border-bottom: 1px solid #cfcfcf; /* horizontal separator */
      }

      /* Rounded top corners for header only */
      table.packet-table thead th:first-child {
        border-top-left-radius: 14px;
      }
      table.packet-table thead th:last-child {
        border-top-right-radius: 14px;
      }

      /* Body cells: only right and bottom borders */
      table.packet-table tbody td {
        padding: 6px;
        border-top: 1px solid #cfcfcf; /* vertical separator */
        border-left: 1px solid #cfcfcf; /* vertical separator */
        border-right: 1px solid #cfcfcf; /* vertical separator */
        border-bottom: 1px solid #cfcfcf; /* horizontal separator */
      }

      /* Grouped row separator: thin line */
      table.packet-table tbody tr.grouped-row td {
        border-bottom: none;
      }

      table.packet-table tbody tr.grouped-row-child td {
        border-top: none;
      }

      /* Enforce right border for last column */
      table.packet-table th:last-child,
      table.packet-table td:last-child {
        border-right: 1px solid #cfcfcf;
      }
    </style>

    <div class="packet-table-wrapper">
    <table class="table table-bordered packet-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Service Provider</th>
          <th>Title</th>
          <th>Version</th>
          <th>Action</th>
        </tr>
      </thead>
      <tbody>
  `;

  if (packets.length > 0) {
    const groupedPackets = packets.reduce((groups, packet) => {
      const key = packet.name;
      if (!groups[key]) groups[key] = [];
      groups[key].push(packet);
      groups[key].sort((a, b) =>
        a.release_version.localeCompare(b.release_version)
      );
      groups[key].forEach(
        (p) => (p.exists = groups[key].some((x) => x.installed))
      );
      return groups;
    }, {});

    Object.keys(groupedPackets).forEach((name) => {
      const rows = groupedPackets[name];
      rows.forEach((doc, index) => {
        const isGroupedRow = rows.length > 1; // all but first row in group
        let rowClass = "";
        if (isGroupedRow) {
          rowClass =
            index > 0 ? 'class="grouped-row-child"' : 'class="grouped-row"';
        }
        htmlContent += `<tr ${rowClass}>`;

        // first row: show name, service provider, title with rowspan
        if (index === 0) {
          htmlContent += `<td rowspan="${rows.length}">${name}</td>`;
          htmlContent += `<td rowspan="${rows.length}">${doc.service_provider}</td>`;
          htmlContent += `<td rowspan="${rows.length}">${doc.title}</td>`;
        }

        // always show version & action
        htmlContent += `
          <td>${doc.release_version}</td>
          <td>
            <span style="color: green; display:${
              doc.installed ? "inline" : "none"
            }">Installed</span>
            <button class="btn btn-default btn-xs"
              style="display:${
                !doc.installed && doc.exists ? "inline" : "none"
              }"
              onclick="handleInstall('${doc.name}','${
          doc.release_version
        }','UPDATE')">
              <span style="color: blue">Update</span>
            </button>
            <button class="btn btn-default btn-xs"
              style="display:${
                !doc.installed && !doc.exists ? "inline" : "none"
              }"
              onclick="handleInstall('${doc.name}','${
          doc.release_version
        }','INSTALL')">
              <span style="color: orange">Install</span>
            </button>
          </td>
        `;
        htmlContent += `</tr>`;
      });
    });
  } else {
    htmlContent += `
      <tr>
        <td colspan="5" class="text-center">
          <img src="/assets/frappe/images/ui-states/grid-empty-state.svg"
               alt="Grid Empty State" class="grid-empty-illustration">
          No Data
        </td>
      </tr>`;
  }

  htmlContent += `
      </tbody>
    </table>
    </div>
  `;

  frm.set_df_property("packages", "options", htmlContent);
  frm.refresh_field("packages");
}

frappe.provide("frappe.ui.misc");
frappe.ui.misc.about = function () {
  if (!frappe.ui.misc.about_dialog) {
    var d = new frappe.ui.Dialog({ title: __("Frappe Framework") });

    $(d.body).html(
      repl(
        `<div>
					<h4>${__("Installed Apps")}</h4>
					<div id='about-app-versions'>${__("Loading versions...")}</div>
					<hr>
					<p class='text-muted'>${__(
            "&copy; Frappe Technologies Pvt. Ltd. and contributors"
          )} </p>
					</div>`,
        frappe.app
      )
    );

    frappe.ui.misc.about_dialog = d;
    let serverBoxInfo = null;
    frappe.ui.misc.about_dialog.on_page_show = function () {
      if (!frappe.versions) {
        frappe.call({
          method:
            "cloud_base_app.cloud_base_app.controllers.box_info_controller.get_local_server_box_info",
          callback: function (r) {
            if (r.message) {
              serverBoxInfo = r.message;
            }
          },
        });
        frappe.call({
          method: "frappe.utils.change_log.get_versions",
          callback: function (r) {
            console.log("Versions fetched", r.message);
            show_versions(r.message);
          },
        });
      } else {
        show_versions(frappe.versions);
      }
    };

    var show_versions = function (versions) {
      var $wrap = $("#about-app-versions").empty();
      $.each(Object.keys(versions).sort(), function (i, key) {
        var v = versions[key];
        let text;
        if (v.branch) {
          text = $.format("<p><b>{0}:</b> v{1} ({2})<br></p>", [
            v.title,
            v.branch_version || v.version,
            v.branch,
          ]);
        } else {
          text = $.format("<p><b>{0}:</b> v{1}<br></p>", [v.title, v.version]);
        }
        $(text).appendTo($wrap);
      });

      if (serverBoxInfo) {
        $("<hr>").appendTo($wrap);
        $("<h4>Box Information</h4>").appendTo($wrap);
        $(
          "<p><b>Mission Controller Version:</b> " +
            (serverBoxInfo.mission_controller_version || "-") +
            "</p>"
        ).appendTo($wrap);
        $(
          "<p><b>Server Box Version:</b> " +
            (serverBoxInfo.server_box_version || "-") +
            "</p>"
        ).appendTo($wrap);
      }

      frappe.versions = versions;
    };
  }

  frappe.ui.misc.about_dialog.show();
};

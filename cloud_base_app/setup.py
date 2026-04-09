import subprocess
import frappe
from frappe.utils.background_jobs import get_jobs

# will run after app is installed on site
def after_install():
    # box_type read from site config
    box_type = frappe.get_conf().get("box_type")
    # insert Box Settings with box_type
    doc = frappe.new_doc("Box Settings")
    doc.box_type = box_type
    doc.insert()

    tenant_code = frappe.get_conf().get("tenant_code")
    tenant_name = frappe.get_conf().get("tenant_name")
    tenant = frappe.new_doc("Tenant Settings")
    tenant.tenant_code = tenant_code
    tenant.tenant_name = tenant_name
    tenant.insert()
    frappe.db.commit()
    pass

# will run after migrate
def after_migrate():
    pass

# todo: we need to handle exceptions
def migrate_and_clear_site():
  subprocess.run(["echo", "-e", f"Migration starter"], cwd="..")
  migrate = subprocess.Popen(["bench", "--site", f"{frappe.local.site}", "migrate"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd="..")
  output, error = migrate.communicate()
  return_code = migrate.wait()
  if return_code != 0:
    raise Exception(error.decode("utf-8"))

  # run bench clear-cache
  clear_cache = subprocess.Popen(["bench", "--site", f"{frappe.local.site}", "clear-cache"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd="..")
  output, error = clear_cache.communicate()
  return_code = clear_cache.wait()
  if return_code != 0:
    raise Exception(error.decode("utf-8"))
  
  enqueued_method = "cloud_base_app.setup.restart_from_host"
  jobs = get_jobs()
  if not jobs or enqueued_method not in jobs[frappe.local.site]:
    frappe.enqueue(enqueued_method, queue="default", enqueue_after_commit=True)
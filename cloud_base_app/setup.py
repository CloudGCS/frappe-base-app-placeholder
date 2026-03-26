import subprocess
import frappe
from frappe.utils.background_jobs import get_jobs
from frappe.utils.password import update_password

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
    
    # Set password for aircraft observer user
    set_aircraft_observer_password()
    pass

# will run after migrate
def after_migrate():
    # Ensure aircraft observer user password is properly set after migrations
    set_aircraft_observer_password()

def set_aircraft_observer_password():
    """Set the password for the aircraft observer user"""
    observer_email = "aircraft-observer@cloudgcs.com"
    
    # Read password from site config for security (not hardcoded)
    # Add to site_config.json: "aircraft_observer_password": "your_password"
    observer_password = frappe.get_conf().get("aircraft_observer_password")
    
    # If not in config, try to get from Aircraft Observing Invite SingleDocType
    if not observer_password:
        try:
            invite_doc = frappe.get_single("Aircraft Observing Invite")
            observer_password = invite_doc.observer_password
        except:
            pass
    
    # If still no password, log warning and skip
    if not observer_password:
        frappe.logger().warning(
            f"No password configured for {observer_email}. "
            "Add 'aircraft_observer_password' to site_config.json or set it in Aircraft Observing Invite."
        )
        return
    
    # Check if user exists
    if frappe.db.exists("User", observer_email):
        try:
            # Update password using Frappe's password utility
            # This properly hashes the password
            update_password(user=observer_email, pwd=observer_password)
            frappe.db.commit()
            frappe.logger().info(f"Password updated for {observer_email}")
        except Exception as e:
            frappe.logger().error(f"Failed to update password for {observer_email}: {str(e)}")

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

def restart_from_host():
  restart_from_host = frappe.get_conf().get("restart_from_host")
  if restart_from_host and restart_from_host == "True":
    # write 'restart' to /hostpipe/reader
    with open('/hostpipe/reader', 'w') as reader:
      reader.write('restart')
      reader.write('haydi-bakem')
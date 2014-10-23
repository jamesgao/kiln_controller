import os

basepath = os.path.join(os.environ['HOME'], ".config", "pipid")
profile_path = os.path.join(basepath, "profiles")
log_path = os.path.join(basepath, "logs")

if not os.path.exists(profile_path):
	os.makedirs(profile_path)
if not os.path.exists(log_path):
	os.makedirs(log_path)

cwd = os.path.abspath(os.path.split(__file__)[0])
html_static = os.path.join(cwd, "static")
html_templates = os.path.join(cwd, "templates")
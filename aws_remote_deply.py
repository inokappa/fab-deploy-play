from fabric.api import local, run, env, cd, lcd, execute, put, sudo
from boto.ec2 import EC2Connection, get_region, connect_to_region

## Please change following to your environment

def default_path():
  env.app = "APP_NAME"
  env.app_repo = "https://github.com/your_account/APP_NAME.git"
  env.snap_shot = "%(app)s-1.0-SNAPSHOT" % { 'app':env.app }
  env.snap_shot_zip = "%(snap_shot)s.zip" % { 'snap_shot':env.snap_shot }
  env.base_dir = "/path/to/app"
  env.deploy_dir = "/path/to/deploy"
  env.current_path = "%(base_dir)s/current" % { 'base_dir':env.base_dir }
  env.releases_path = "%(base_dir)s/releases" % { 'base_dir':env.base_dir }

def your_environment(tag = "Name", value = "YOUR_NAME_TAG_VALUE", region = "REGION"):
  key = "tag:"+tag
  env.hosts = _get_private_ip(region, key, value)

################################################

def _get_host_ip(region, key, value ="*"):
  private_ip = []
  conn = _create_connection(region)
  reservations = conn.get_all_instances(filters = {key : value})
  for reservation in reservations:
      for instance in reservation.instances:
          print "Instance", instance.private_ip_address
          private_ip.append(str(instance.private_ip_address))
  return private_ip

def _create_connection(region):
  print "Connecting to ", region
  conn = connect_to_region(
      region_name = region
  )
  print "Connection with AWS established"
  return conn

def set_path():
  execute(default_path)
  env.releases = sorted(run('ls -x %(releases_path)s' % { 'releases_path':env.releases_path }).split())
  if len(env.releases) >= 1:
    env.current_revision = env.releases[-1]
    env.current_release = "%(releases_path)s/%(current_revision)s" % { 'releases_path':env.releases_path, 'current_revision':env.current_revision }
  if len(env.releases) > 1:
    env.previous_revision = env.releases[-2]
    env.previous_release = "%(releases_path)s/%(previous_revision)s" % { 'releases_path':env.releases_path, 'previous_revision':env.previous_revision }

def dist_setup():
  execute(default_path)
  local('mkdir -p %(deploy_dir)s' % { 'deploy_dir':env.deploy_dir })

def remote_setup():
  execute(default_path)
  run('mkdir -p %(base_dir)s/releases' % { 'base_dir':env.base_dir} )

def dist_package():
  execute(default_path)
  with lcd('%(deploy_dir)s/' % { 'deploy_dir':env.deploy_dir }):
    local('if [ -d %(app)s ]; then rm -rf %(app)s ; fi' % { 'app':env.app })
    local('git clone %(app_repo)s' % { 'app_repo': env.app_repo })
  with lcd('%(deploy_dir)s/%(app)s' % { 'deploy_dir':env.deploy_dir, 'app':env.app }):
    local('play dist')

def deploy():
  execute(set_path)
  from time import time
  env.current_release = '%(releases_path)s/%(time).0f' % { 'releases_path':env.releases_path, 'time':time() }
  with lcd('%(deploy_dir)s/%(app)s/target/universal/' % { 'deploy_dir':env.deploy_dir, 'app':env.app, 'base_dir':env.base_dir }):
    local('ls %(snap_shot)s' % { 'snap_shot':env.snap_shot })
    put( env.snap_shot_zip, '%(base_dir)s/' % { 'base_dir':env.base_dir })
  with cd ('%(base_dir)s/' % { 'base_dir':env.base_dir }):
    run('unzip %(snap_shot)s -d %(current_release)s/' % { 'current_release':env.current_release, 'snap_shot':env.snap_shot })
  run('ln -nfs %(current_release)s %(current_path)s' % { 'current_release':env.current_release , 'current_path':env.current_path })

def app_status():
  execute(default_path)
  sudo('supervisorctl status %(app)s' % { 'app':env.app }, pty=True, shell=False)

def app_start():
  execute(set_path)
  with cd("%(current_path)s/%(snap_shot)s/" % { 'current_path':env.current_path, 'snap_shot':env.snap_shot }):
    run('if [ -f RUNNING_PID ]; then rm RUNNING_PID ; fi')
  sudo('supervisorctl start %(app)s' % { 'app':env.app }, pty=True, shell=False)

def app_stop():
  execute(default_path)
  sudo('supervisorctl stop %(app)s' % { 'app':env.app }, pty=True, shell=False)

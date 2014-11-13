from fabric.api import local, run, env, cd, lcd, execute, put

def set_path():
  env.app = "your_application"
  env.snap_shot = "%(app)s-1.0-SNAPSHOT" % { 'app':env.app }
  env.base_dir = "/path/to/prod"
  env.deploy_dir = "/path/to/deploy"
  env.current_path = "%(base_dir)s/current" % { 'base_dir':env.base_dir }
  env.releases_path = "%(base_dir)s/releases" % { 'base_dir':env.base_dir }

  env.releases = sorted(local('ls -x %(releases_path)s' % { 'releases_path':env.releases_path }).split())
  if len(env.releases) >= 1:
    env.current_revision = env.releases[-1]
    env.current_release = "%(releases_path)s/%(current_revision)s" % { 'releases_path':env.releases_path, 'current_revision':env.current_revision }
  if len(env.releases) > 1:
    env.previous_revision = env.releases[-2]
    env.previous_release = "%(releases_path)s/%(previous_revision)s" % { 'releases_path':env.releases_path, 'previous_revision':env.previous_revision }

def setup():
  execute(set_path)
  with lcd('%(deploy_dir)s/%(app)s/' % { 'deploy_dir':env.deploy_dir, 'app':env.app }):
    local('rm %(deploy_dir)s/%(app)s/target/universal/*.zip' % { 'deploy_dir':env.deploy_dir, 'app':env.app })
    local('play dist')

def app_stop():
  execute(set_path)
  with lcd('%(current_path)s/%(snap_shot)s/' % { 'current_path':env.current_path, 'snap_shot':env.snap_shot }):
    local('kill `cat RUNNING_PID`')
    local('rm -f RUNNING_PID')

def app_start():
  execute(set_path)
  with lcd('%(current_path)s/%(snap_shot)s/' % { 'current_path':env.current_path, 'snap_shot':env.snap_shot }):
    local('if [ -f RUNNING_PID ]; then rm RUNNING_PID ; fi')
  with lcd('%(current_path)s/%(snap_shot)s/bin/' % { 'current_path':env.current_path, 'snap_shot':env.snap_shot }):
    local('./hoge &')
    local('sleep 5')

def deploy():
  execute(set_path)
  execute(setup)
  from time import time
  env.current_release = "%(releases_path)s/%(time).0f" % { 'releases_path':env.releases_path, 'time':time() }
  local('cp %(deploy_dir)s/%(app)s/target/universal/%(snap_shot)s.zip %(base_dir)s/' % { 'deploy_dir':env.deploy_dir, 'base_dir':env.base_dir, 'snap_shot':env.snap_shot, 'app':env.app })
  with lcd ("%(base_dir)s/" % { 'base_dir':env.base_dir }):
    local('unzip %(snap_shot)s.zip -d %(current_release)s/' % { 'current_release':env.current_release, 'snap_shot':env.snap_shot })
  local('ln -nfs %(current_release)s %(current_path)s' % { 'current_release':env.current_release , 'current_path':env.current_path })

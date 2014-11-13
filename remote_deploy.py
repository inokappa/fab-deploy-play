from fabric.api import local, run, env, cd, execute, put, sudo

def default_path():
  env.app = "app_name"
  env.app_repo = "https://github.com/user/app_name.git"
  env.snap_shot = "%(app)s-1.0-SNAPSHOT" % { 'app':env.app }
  env.base_dir = "/path/to/prod"
  env.deploy_dir = "/path/to/deploy"
  env.current_path = "%(base_dir)s/current" % { 'base_dir':env.base_dir }
  env.releases_path = "%(base_dir)s/releases" % { 'base_dir':env.base_dir }

def set_path():
  execute(default_path)
  env.releases = sorted(run('ls -x %(releases_path)s' % { 'releases_path':env.releases_path }).split())
  if len(env.releases) >= 1:
    env.current_revision = env.releases[-1]
    env.current_release = "%(releases_path)s/%(current_revision)s" % { 'releases_path':env.releases_path, 'current_revision':env.current_revision }
  if len(env.releases) > 1:
    env.previous_revision = env.releases[-2]
    env.previous_release = "%(releases_path)s/%(previous_revision)s" % { 'releases_path':env.releases_path, 'previous_revision':env.previous_revision }

def setup():
  execute(default_path)
  run('mkdir -p %(base_dir)s/releases' % { 'base_dir':env.base_dir} )
  run('mkdir -p %(deploy_dir)s' % { 'deploy_dir':env.deploy_dir })

def dist_package():
  execute(set_path)
  with cd('%(deploy_dir)s/' % { 'deploy_dir':env.deploy_dir }):
    run('if [ -d %(app)s ]; then rm -rf %(app)s ; fi' % { 'app':env.app })
    run('git clone %(app_repo)s' % { 'app_repo': env.app_repo })
  with cd('%(deploy_dir)s/%(app)s' % { 'deploy_dir':env.deploy_dir, 'app':env.app }):
    run('play dist')

def deploy():
  execute(set_path)
  execute(dist_package)
  from time import time
  env.current_release = "%(releases_path)s/%(time).0f" % { 'releases_path':env.releases_path, 'time':time() }
  run('cp %(deploy_dir)s/%(app)s/target/universal/%(snap_shot)s.zip %(base_dir)s/' % { 'deploy_dir':env.deploy_dir, 'app':env.app, 'base_dir':env.base_dir, 'snap_shot':env.snap_shot })
  with cd ("%(base_dir)s/" % { 'base_dir':env.base_dir }):
    run('unzip %(snap_shot)s.zip -d %(current_release)s/' % { 'current_release':env.current_release, 'snap_shot':env.snap_shot })
  run('ln -nfs %(current_release)s %(current_path)s' % { 'current_release':env.current_release , 'current_path':env.current_path })

def app_status():
  execute(set_path)
  sudo('supervisorctl status %(app)s' % { 'app':env.app }, pty=True, shell=False)

def app_start():
  execute(set_path)
  with cd('%(current_path)s/%(snap_shot)s/' % { 'current_path':env.current_path, 'snap_shot':env.snap_shot }):
    run('if [ -f RUNNING_PID ]; then rm RUNNING_PID ; fi')
  sudo('supervisorctl start %(app)s' % { 'app':env.app }, pty=True, shell=False)

def app_stop():
  execute(set_path)
  sudo('supervisorctl stop %(app)s' % { 'app':env.app }, pty=True, shell=False)

# -*- coding: utf-8 -*-

from fabric.api import run, cd

from mc.exceptions import InstanceIsRunning

from django.conf import settings


def _mysql_command(host, cmd):
    return ("/usr/bin/mysql -h localhost -u '%s' '--password=%s' -P %s -e \"" % \
            (host.admin_user, host.admin_password, host.port,)) + cmd + "\""


def _get_instance_path(instance):
    return "%s/%s" % (instance.yigo_host.root_path, instance.id,)

def _get_log4j_configuration(instance):
    return r"log4j.appender.LOGSTASH=org.apache.log4j.net.SocketAppender\nlog4j.appender.LOGSTASH.remoteHost=%s\nlog4j.appender.LOGSTASH.port=%s\nlog4j.appender.LOGSTASH.locationInfo=true\nlog4j.appender.LOGSTASH.application=%s\nlog4j.rootLogger=INFO,LOGSTASH\n" % (settings.LOGSTASH_HOST, settings.LOGSTASH_PORT, instance.id)

def delete_mysql_instance(instance):
    """Delete database and user on remote mysql instance.

    Paramters
    ---------
    instance : mc.models.YigoInstance
    """
    if is_yigo_instance_running(instance):
        raise InstanceIsRunning()

    host = instance.database_host
    database = instance.database_name()
    user = instance.database_user()

    cmd_drop_user = _mysql_command(host, "drop user '%s'@'%%';" % (user,) )
    cmd_drop_database = _mysql_command(host, "drop database %s;" % (database,))
    run(cmd_drop_user, quiet=True)
    run(cmd_drop_database, quiet=True)


def delete_yigo_instance(instance):
    if is_yigo_instance_running(instance):
        raise InstanceIsRunning()

    run("rm -rf %s" % (_get_instance_path(instance),), quiet=True)


def create_mysql_instance(instance):
    """Create database and user on remote mysql instance.

    Parameters
    ----------
    instance : mc.models.YigoInstance
    """
    host = instance.database_host
    database = instance.database_name()
    user = instance.database_user()
    password = instance.database_password
    cmd_create_database = _mysql_command(host, "create database %s;" % (database,))
    cmd_create_user = _mysql_command(host, "create user '%s'@'%%' identified by '%s';" % (user, password,))
    cmd_grant = _mysql_command(host, "grant all on %s.* to '%s'@'%%';" % (database, user,))
    run(cmd_create_database)
    run(cmd_create_user)
    run(cmd_grant)


def create_yigo_instance(instance):
    """Create yigo instance directory layout, install yigo release pack and yigo app config pack.
    The process is completed successfully if no `Exception' raised.

    Parameters
    ----------
    instance : mc.models.YigoInstance
    """
    instance_code = instance.external_id
    configs_source = instance.configs_source
    configs_filename = configs_source.split('/')[-1]
    checksum_source = configs_source + '.sha256sum'
    checksum_filename = configs_filename + '.sha256sum'
    instance_path = _get_instance_path(instance)
    run("mkdir -p %s/{cache,configs,data,logs,tmp,yigo}" % (instance_path,))
    run("tar -xf yigo-%s.tar.gz -C %s/yigo" % (instance.yigo_env.version, instance_path,))
    run("echo -e \"" + _get_log4j_configuration(instance) + \
        ("\" > %s/yigo/WEB-INF/classes/log4j.properties" % (instance_path,)))
    with cd('%s/cache' % (instance_path,)):
        # All timeout of wget are set to 2 seconds
        run("wget -q -T 2 -O '%s' '%s'" % (checksum_filename, checksum_source,))
        run("wget -q -T 2 -O '%s' '%s'" % (configs_filename, configs_source,))
        run("sha256sum -c '%s'" % (checksum_filename,))
        run("tar -xf '%s' -C '../configs'" % (configs_filename,))
        run("test -e  ../configs/_yigo && cp -a ../configs/_yigo/* ../yigo/")

def _get_pid_filename(instance):
    return '%s/tmp/pid' % (_get_instance_path(instance),)


def is_yigo_instance_running(instance):
    """
    Test whether instance is running.

    Paratmers
    ---------
    instance : mc.models.YigoInstance
    """
    instance_code = instance.external_id
    pid_filename = _get_pid_filename(instance)
    return run("test -e '%s' && ps -f -p $(<'%s') | grep 'yigo.instance=%s'" %
               (pid_filename, pid_filename, instance_code,), quiet=True).succeeded


def start_yigo_instance(instance):
    """
    Start JVM to run yigo instance.

    Parameters
    ----------
    instance : mc.models.YigoInstance
    """
    if is_yigo_instance_running(instance):
        raise InstanceIsRunning()
    else:
        instane_code = instance.external_id
        # Find java command
        java_home = instance.java_env.path
        if java_home[-1] != '/':
            java_home = java_home + '/'
        java_exec = java_home + 'bin/java'
        # Process command arguments
        args = [java_exec, '-server']
        # Memory
        args.append('-Xms%sm' % (instance.yigo_host.heap_size,))
        args.append('-Xmx%sm' % (instance.yigo_host.heap_size,))
        args.append('-XX:MaxPermSize=128m')
        # Classpath
        args.append('-cp')
        args.append('"yigo/WEB-INF/classes:yigo/WEB-INF/lib/*:yigo/WEB-INF/lib/@deprecated/*:yigo/WEB-INF/lib/@deprecated/jetty/*"')
        # Yigo properties
        args.append('-Dserver.cloudregisterserver=http://1.1.8.16:8080/yigo')
        args.append('-Dserver.config=configs/main')
        args.append('-Dserver.generateYigoCss=false')
        args.append('-Dserver.dsn.description=default')
        args.append('-Dserver.dsn.default=Y')
        args.append('-Dserver.dsn.dbtype=3')
        args.append('-Dserver.dsn.name=default')
        args.append('-Dserver.db.default.conntype=jdbc')
        args.append('-Dserver.db.default.dbtype=3')
        args.append('-Dserver.db.default.driver=com.mysql.jdbc.Driver')
        args.append('\'-Dserver.db.default.url=jdbc:mysql://%s:%s/%s?useUnicode=true&amp;characterEncoding=UTF-8\'' %
                    (instance.database_host.address, instance.database_host.port, instance.database_name(),))
        args.append('-Dserver.db.default.user=%s' % (instance.database_user(),))
        args.append('-Dserver.db.default.pass=%s' % (instance.database_password,))
        args.append('-DCODEBASE_SERVICE=yigo')
        args.append('-DAPP_SERVICE=yigo')
        args.append('-DAPP_SERVER=localhost:%s' % (instance.service_port,))
        # Instance properties
        args.append('-Dyigo.home=yigo')
        args.append('-Dyigo.instance=%s' % (instance.external_id,))
        args.append('-Djava.io.tmpdir=tmp')
        # Main class
        args.append('test.start.StartHttpServer')
        # Arguments of main class
        args.append('yigo') # yigo install dir
        args.append('\'core@cloud\'') # empty core.properties

        cmd = ' '.join(args)
        with cd(_get_instance_path(instance)):
            # Use `sleep 1` to wait the command starting up before fabric closes the ssh connection
            run('$(nohup ' + cmd + ' >& logs/nohup.out < /dev/null & echo $! > tmp/pid) && sleep 1')


def stop_yigo_instance(instance, force=False):
    signal = 'TERM'
    if force: signal = 'KILL'
    pid_filename = _get_pid_filename(instance)
    if is_yigo_instance_running(instance):
        run("kill -s %s $(<'%s') && rm '%s'" % (signal, pid_filename, pid_filename))



# Local Variables: **
# comment-column: 56 **
# indent-tabs-mode: nil **
# python-indent: 4 **
# End: **

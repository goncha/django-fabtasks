# -*- coding: utf-8 -*-

from django.db import transaction
from django.db.models import F

from mc.exceptions import *

from mc.models import *
from mc.jsonrpc import *
from mc.utils import *


def get_host(instance):
    yigo_host = instance.yigo_host
    return '%s@%s:%s' % (yigo_host.ssh_user, yigo_host.address, yigo_host.ssh_port,)

def initialize_fabric():
    from fabric import state
    from fabric.main import load_tasks_from_module
    import fabtasks
    docstring, new_style, classic, default = load_tasks_from_module(fabtasks)
    tasks = new_style if state.env.new_style_tasks else classic
    state.commands.update(tasks)
    state.env['key_filename'] = 'key/id_rsa'
    state.env['abort_exception'] = RuntimeError # Use exception to abort failed commands
initialize_fabric()


from fabric.api import execute


def busymethod(method):
    def wrapper(self, pk, *args, **kwargs):
        if not YigoInstance.objects.filter(pk=pk, busy=False).update(busy=True):
            YigoInstance.objects.get(pk=pk) # checking instance exists, will raise DoesNotExist
            raise InstanceIsBusy()
        try:
            return method(self, pk, *args, **kwargs)
        finally:
            YigoInstance.objects.filter(pk=pk, busy=True).update(busy=False)
    return wrapper


class Manager(object):

    def _find_sparest_host(self, host_type):
        spare_hosts = host_type.objects.filter(max_instances__gt=0)
        if spare_hosts:
            return sorted(spare_hosts, key=lambda x: x.instance_set.count())[0]
        else:
            raise NoMoreSpareHosts(host_type)

    def _find_service_port(self, yigo_host):
        if yigo_host.instance_set.count() == 0:
            return yigo_host.initial_service_port
        else:
            instances = yigo_host.instance_set.all().order_by('service_port')
            for i, instance in enumerate(instances):
                if instance.service_port != yigo_host.initial_service_port + i:
                    return yigo_host.initial_service_port + i
            return yigo_host.initial_service_port + len(instances)

    def _find_env(self, env_type, version=None):
        envs = None
        if version:
            envs = env_type.objects.filter(version=version)
        else:
            envs = env_type.objects.all().order_by('-version')
        if envs:
            return envs[0]
        else:
            raise NoEnv(env_type, version)

    def _check_is_running(self, pk):
        if self.is_running(pk):
            raise InstanceIsRunning()


    def create(self, instance_code, configs_source, yigo_version=None, java_version=None):
        yigo_host = self._find_sparest_host(YigoHost)
        service_port = self._find_service_port(yigo_host)
        database_host = self._find_sparest_host(DatabaseHost)
        java_env = self._find_env(JavaEnv, java_version)
        yigo_env = self._find_env(YigoEnv, yigo_version)

        instance = YigoInstance(external_id=instance_code,
                                yigo_host=yigo_host,
                                configs_source=configs_source,
                                service_port=service_port,
                                database_host=database_host,
                                java_env=java_env,
                                yigo_env=yigo_env)

        with transaction.atomic():
            instance.save()

        return {'id': instance.id,
                'url': 'http://%s:%s/%s/' %  (yigo_host.address, instance.service_port, 'yigo',)}


    def info(self, pk):
        instance = YigoInstance.objects.get(pk=pk)
        return {
            'id': instance.id,
            'external_id': instance.external_id,
            'java_env': instance.java_env.version,
            'yigo_env': instance.yigo_env.version,
            'yigo_heap_size_in_mb': instance.yigo_host.heap_size
        }


    @busymethod
    def install(self, pk):
        instance = YigoInstance.objects.get(pk=pk)
        self._check_is_running(pk)

        host = get_host(instance)
        # recreate mysql instance
        execute('delete_mysql_instance', hosts=[host], *[instance], **{})
        instance.database_installed = False
        instance.save()
        execute('create_mysql_instance', hosts=[host], *[instance], **{})
        instance.database_installed = True
        instance.save()
        # recreate yigo instance
        execute('delete_yigo_instance', hosts=[host], *[instance], **{})
        instance.installed = False
        instance.save()
        execute('create_yigo_instance', hosts=[host], *[instance], **{})
        instance.installed = True
        instance.save()


    @busymethod
    def uninstall(self, pk):
        instance = YigoInstance.objects.get(pk=pk)
        self._check_is_running(pk)

        host = get_host(instance)
        if instance.installed:
            execute('delete_yigo_instance', hosts=[host], *[instance], **{})
            instance.installed = False
            instance.save()
        if instance.database_installed:
            execute('delete_mysql_instance', hosts=[host], *[instance], **{})
            instance.database_installed = False
            instance.save()

    @busymethod
    def start(self, pk):
        instance = YigoInstance.objects.get(pk=pk)
        self._check_is_running(pk)

        if instance.installed and instance.database_installed:
            host = get_host(instance)
            execute('start_yigo_instance', hosts=[host], *[instance], **{})
        else:
            raise InstanceNotInstalled()

    @busymethod
    def stop(self, pk):
        instance = YigoInstance.objects.get(pk=pk)
        if instance.installed and instance.database_installed:
            host = get_host(instance)
            execute('stop_yigo_instance', hosts=[host], *[instance], **{})
        else:
            raise InstanceNotInstalled()


    def is_running(self, pk):
        instance = YigoInstance.objects.get(pk=pk)
        if instance.installed and instance.database_installed:
            host = get_host(instance)
            result = execute('is_yigo_instance_running', hosts=[host], *[instance], **{})
            return result[host]
        return False




# Local Variables: **
# comment-column: 56 **
# indent-tabs-mode: nil **
# python-indent: 4 **
# End: **

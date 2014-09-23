from django.db import models

HEAP_SIZES = (
    (1024, '1GB'),
    (512, '512MB'),
    (256, '256MB'),
)


class YigoEnv(models.Model):
    version = models.CharField(max_length=20, unique=True)
    path    = models.CharField(max_length=100)

    def __unicode__(self):
        return self.version


class JavaEnv(models.Model):
    version = models.CharField(max_length=20, unique=True)
    path    = models.CharField(max_length=100)

    def __unicode__(self):
        return self.version


class RemoteHost(models.Model):
    address             = models.CharField(max_length=50, help_text='address of this host')
    ssh_user            = models.CharField(max_length=50, help_text='user for ssh connection to this host')
    ssh_port            = models.IntegerField(default=22, help_text='ssh port of this host')
    max_instances       = models.IntegerField(default=1, help_text='max number of instances this host can afford')

    def __unicode__(self):
        return '%s@%s:%s' % (self.ssh_user, self.address, self.ssh_port)

    class Meta:
        abstract = True


class YigoHost(RemoteHost):
    heap_size            = models.IntegerField(choices=HEAP_SIZES, help_text='JVM max heap size (MB) on this host')
    root_path            = models.CharField(max_length=100, default='apps', help_text='root path of installed instances')
    initial_service_port = models.IntegerField(default=8000, help_text='initial service port of installed instances')


class DatabaseHost(RemoteHost):
    admin_user     = models.CharField(max_length=50, help_text='admin user of database')
    admin_password = models.CharField(max_length=50, help_text='admin password of database')
    port           = models.IntegerField(default=3306, help_text='port of database service')


class YigoInstance(models.Model):
    external_id = models.CharField(max_length=100, unique=True, help_text='instance id in external system')

    yigo_host      = models.ForeignKey(YigoHost, related_name='instance_set')
    configs_source = models.URLField(max_length=200, help_text='URL of instance configs for downloading')
    service_port   = models.IntegerField(default=8000, help_text='service port of this instance')
    installed      = models.BooleanField(default=False, help_text='is this instance installed successfully')

    database_host      = models.ForeignKey(DatabaseHost, related_name='instance_set')
    database_password  = models.CharField(max_length=50, help_text='database password for this instance')
    database_installed = models.BooleanField(default=False, help_text='is database installed successfully')

    yigo_env = models.ForeignKey(YigoEnv, related_name='+')
    java_env = models.ForeignKey(JavaEnv, related_name='+')

    busy = models.BooleanField(default=False, help_text='is this instance busy on task')

    def database_name(self):
        return 'u%d' % (self.pk,)

    def database_user(self):
        return 'u%d' % (self.pk,)

    def __unicode__(self):
        return self.external_id

    class Meta:
        unique_together = (('yigo_host', 'service_port'),)


from django.dispatch import receiver
from django.db.models import signals, F
from mc.exceptions import NoMoreSpareHosts, UninstallBeforeDelete
from mc.models import YigoInstance
from mc.utils import generate_password

@receiver(signals.post_init, sender=YigoInstance)
def post_init_yigo_instance(**kwargs):
    instance = kwargs['instance']
    if not instance.database_password:
        instance.database_password = generate_password()

def check_host_refs(host_type, host_instance):
    host_instance = host_type.objects.select_for_update().get(pk=host_instance.pk)
    if host_instance.max_instances <= host_instance.instance_set.count():
        raise NoMoreSpareHosts(host_type)

@receiver(signals.pre_save, sender=YigoInstance)
def pre_save_yigo_instance(**kwargs):
    instance = kwargs['instance']
    if not instance.pk:
        check_host_refs(YigoHost, instance.yigo_host)
        check_host_refs(DatabaseHost, instance.database_host)
    else:
        old_instance = YigoInstance.objects.get(pk=instance.pk)
        if old_instance.yigo_host != instance.yigo_host:
            check_host_refs(YigoHost, instance.yigo_host)
        if old_instance.database_host != instance.database_host:
            check_host_refs(DatabaseHost, instance.database_host)

@receiver(signals.pre_delete, sender=YigoInstance)
def pre_delete_yigo_instance(**kwargs):
    instance = kwargs['instance']
    if instance.installed or instance.database_installed:
        raise UninstallBeforeDelete()

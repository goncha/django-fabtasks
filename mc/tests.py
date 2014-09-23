from django.test import TestCase

from mc.exceptions import *
from mc.models import *
from mc.manager import Manager


CONFIGS_SOURCE = 'http://1.1.2.154/software/yigo/config-tutorial-20140721.tar.gz'
TEST_HOST = '1.1.2.193'


class ManagerTests(TestCase):

    def _create_yigo_host(self, address, max_instances=1):
        self.yigo_host = YigoHost(address=address, ssh_user='cloud', max_instances=max_instances,
                                  heap_size=256)
        self.yigo_host.save()

    def _create_database_host(self, address, max_instances=1):
        self.database_host = DatabaseHost(address=address, ssh_user='cloud', max_instances=max_instances,
                                          admin_user='root', admin_password='root')
        self.database_host.save()

    def _create_yigo_env(self, version):
        self.yigo_env = YigoEnv(version=version, path='yigo-%s.tar.gz'%(version,))
        self.yigo_env.save()

    def _create_java_env(self, version):
        self.java_env = JavaEnv(version='1.6', path='/opt/jdk1.6.0_43')
        self.java_env.save()

    def _setup(self):
        self._create_yigo_host(TEST_HOST)
        self._create_database_host(TEST_HOST)
        self._create_yigo_env('20140721')
        self._create_java_env('1.6')

    def test_no_yigo_hosts_when_creating(self):
        self._create_database_host(TEST_HOST, 1)
        self._create_yigo_env('20140721')
        self._create_java_env('1.6')
        try:
            Manager().create('t1', CONFIGS_SOURCE)
        except NoMoreSpareHosts, e:
            self.assertEqual(e.host_type, YigoHost)

    def test_no_spare_yigo_hosts_when_creating(self):
        self._create_yigo_host(TEST_HOST, 0)
        self._create_database_host(TEST_HOST, 1)
        self._create_yigo_env('20140721')
        self._create_java_env('1.6')
        try:
            Manager().create('t1', CONFIGS_SOURCE)
        except NoMoreSpareHosts, e:
            self.assertEqual(e.host_type, YigoHost)

    def test_no_database_hosts_when_creating(self):
        self._create_yigo_host(TEST_HOST, 1)
        try:
            Manager().create('t1', CONFIGS_SOURCE)
        except NoMoreSpareHosts, e:
            self.assertEqual(e.host_type, DatabaseHost)

    def test_no_spare_database_hosts_when_creating(self):
        self._create_yigo_host(TEST_HOST, 1)
        self._create_database_host(TEST_HOST, 0)
        self._create_yigo_env('20140721')
        self._create_java_env('1.6')
        try:
            Manager().create('t1', CONFIGS_SOURCE)
        except NoMoreSpareHosts, e:
            self.assertEqual(e.host_type, DatabaseHost)

    def test_no_yigo_env_when_creating(self):
        self._create_yigo_host(TEST_HOST)
        self._create_database_host(TEST_HOST)
        self._create_java_env('1.6')
        try:
            Manager().create('t1', CONFIGS_SOURCE)
        except NoEnv, e:
            self.assertEqual(e.env_type, YigoEnv)

    def test_no_java_env_when_creating(self):
        self._create_yigo_host(TEST_HOST)
        self._create_database_host(TEST_HOST)
        self._create_yigo_env('20140721')
        try:
            Manager().create('t1', CONFIGS_SOURCE)
        except NoEnv, e:
            self.assertEqual(e.env_type, JavaEnv)

    def test_creating(self):
        self._setup()
        result = Manager().create('t1', CONFIGS_SOURCE)
        instance = YigoInstance.objects.get(pk=result['id'])
        self.assertFalse(instance.installed)
        self.assertFalse(instance.database_installed)

    def test_hosts_refs_after_creating(self):
        self._setup()
        result = Manager().create('t1', CONFIGS_SOURCE)
        instance = YigoInstance.objects.get(pk=result['id'])
        self.assertEqual(1, YigoHost.objects.get(pk=self.yigo_host.id).instance_set.count())
        self.assertEqual(1, DatabaseHost.objects.get(pk=self.database_host.id).instance_set.count())

    def test_installed_state_before_installing(self):
        self._setup()
        result = Manager().create('t1', CONFIGS_SOURCE)
        instance = YigoInstance.objects.get(pk=result['id'])
        self.assertFalse(instance.installed)
        self.assertFalse(instance.database_installed)

    def test_installed_state_after_installing(self):
        self._setup()
        manager = Manager()
        result = manager.create('t1', CONFIGS_SOURCE)
        id = result['id']
        manager.install(id)
        instance = YigoInstance.objects.get(pk=id)
        self.assertTrue(instance.installed)
        self.assertTrue(instance.database_installed)

    def test_hosts_refs_after_deleting(self):
        self._setup()
        result = Manager().create('t1', CONFIGS_SOURCE)
        instance = YigoInstance.objects.get(pk=result['id'])
        self.assertEqual(1, YigoHost.objects.get(pk=self.yigo_host.id).instance_set.count())
        self.assertEqual(1, DatabaseHost.objects.get(pk=self.database_host.id).instance_set.count())
        instance.delete()
        self.assertEqual(0, YigoHost.objects.get(pk=self.yigo_host.id).instance_set.count())
        self.assertEqual(0, DatabaseHost.objects.get(pk=self.database_host.id).instance_set.count())

    def test_hosts_refs_after_deleting(self):
        self._setup()
        manager = Manager()
        result = manager.create('t1', CONFIGS_SOURCE)
        id = result['id']
        manager.install(id)
        try:
            YigoInstance.objects.get(pk=id).delete()
        except UninstallBeforeDelete:
            pass
        else:
            self.fail('Must raise ' + UninstallBeforeDelete.__name__)

    def test_no_file_on_remote_when_creating(self):
        self._create_yigo_host(TEST_HOST)
        self._create_database_host(TEST_HOST)
        self._create_yigo_env('20140720') # no file for this env
        self._create_java_env('1.6')
        manager = Manager()
        result = manager.create('t1', CONFIGS_SOURCE)
        try:
            manager.install(result['id'])
        except RuntimeError, e:
            self.assertTrue(e.message.find('20140720') > -1)

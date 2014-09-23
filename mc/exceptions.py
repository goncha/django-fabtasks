# -*- coding: utf-8 -*-

class NoMoreSpareHosts(Exception):

    def __init__(self, host_type):
        self.host_type = host_type
        Exception.__init__(self, 'No more spare hosts, %s' % (host_type.__name__,))

class NoEnv(Exception):

    def __init__(self, env_type, env_version):
        self.env_type = env_type
        self.env_version = env_version
        Exception.__init__(self, 'No such %s, %s' % (env_type.__name__, env_version,))


class InstanceNotInstalled(Exception):
    pass

class InstanceAlreadyInstalled(Exception):
    pass

class InstanceIsRunning(Exception):
    pass

class InstanceIsBusy(Exception):
    pass

class RefreshOldData(Exception):
    pass

class UninstallBeforeDelete(Exception):
    pass

# Local Variables: **
# comment-column: 56 **
# indent-tabs-mode: nil **
# python-indent: 4 **
# End: **

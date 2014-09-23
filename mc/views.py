from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt

from mc.jsonrpc import *
from mc.manager import Manager

class RpcMethods(object):

    def __init__(self):
        self.url = reverse('mc:rpc')
        self.manager =  Manager()

    @publicmethod
    def create(self, instance_code, configs_source, yigo_version=None, java_version=None):
        return self.manager.create(instance_code, configs_source, yigo_version, java_version)

    @publicmethod
    def info(self, pk):
        return self.manager.info(pk)

    @publicmethod
    def install(self, pk):
        return self.manager.install(pk)

    @publicmethod
    def uninstall(self, pk):
        return self.manager.uninstall(pk)

    @publicmethod
    def start(self, pk):
        return self.manager.start(pk)

    @publicmethod
    def stop(self, pk):
        return self.manager.stop(pk)

    @publicmethod
    def is_running(self, pk):
        return self.manager.is_running(pk)


@csrf_exempt
def rpc(request):
    rpc     = JsonRpc( RpcMethods() )
    result  = rpc.handle_request(request)
    return result

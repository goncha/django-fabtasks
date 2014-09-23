# -*- coding: utf-8 -*-

from django.contrib import admin
from mc.views import *
from mc.models import *
from mc.manager import *

class YigoEnvAdmin(admin.ModelAdmin):
    list_display = ('version','path')

class JavaEnvAdmin(admin.ModelAdmin):
    list_display = ('version','path')

class YigoHostAdmin(admin.ModelAdmin):
    list_display = ('address', 'ssh_user', 'ssh_port')

class DatabaseHostAdmin(admin.ModelAdmin):
    list_display = ('address', 'ssh_user', 'ssh_port', 'port')

class YigoInstanceAdmin(admin.ModelAdmin):
    list_display    = ('external_id', 'yigo_host', 'service_port', 'installed', 'database_host', \
                       'database_installed')
    readonly_fields = ( 'busy', 'installed', 'database_installed','database_password',)
    actions         = ['install_instance','start_instance','stop_instance','uninstall_instance',]



    def install_instance(self,request,queryset):
        """ 1.安装实例，2.根据instance的id，创建数据库的用户名和密码，注意：external_id必须是以字母开头database_name=external_id,
                                database_user=external_id,'database_name', 'database_name', 'database_user'"""
        instances=queryset
        count=0
        installed_count=0
        for instance in instances:
            external_id=instance.external_id
            queryset.update(database_password=generate_password())
            if instance.installed==False and instance.database_installed==False:
                ins= Manager()
                ins.install(instance.id)
                count+=1
            else:
                installed_count+=1
        if count==0:
            self.message_user(request,"no instances install success")
        else:
            self.message_user(request,"%s instances new install and %s instances had been installed before this time"%(count ,installed_count,))



    def start_instance(self,request,queryset):
        """启动实例"""
        instances=queryset
        count=0
        start_count=0
        for instance in instances:
            if instance.installed==True and instance.database_installed==True:
                ins=Manager()
                if ins.is_running(instance.id)==True:
                   start_count+=1
                else:
                    ins.start(instance.id)
                    count+=1
            else:
                pass
        if count==0:
            self.message_user(request,"no instances start")
        else:
            self.message_user(request,"start %s instances success and %s instances is running" %(count ,start_count,))


    def stop_instance(self,request,queryset):
        """停止实例"""
        instances=queryset
        count=0
        for instance in instances:
            if instance.installed==False and instance.database_installed==False:
                pass
            else:
                ins=Manager()
                if ins.is_running(instance.id)==True:
                    ins.stop(instance.id)
                    count+=1
                else:
                    pass
        self.message_user(request,"stop %s  instances success" %count)

    def uninstall_instance(self,request,queryset):
        """ 删除实例"""
        instances=queryset
        count=0
        for instance in instances:
            if instance.installed==False and instance.database_installed==False:
               pass
            else:
                ins=Manager()
                if ins.is_running(instance.id)==True:
                    ins.stop(instance.id)
                    ins.uninstall(instance.id)
                    count+=1
                else:
                    ins.uninstall(instance.id)
                    count+=1
        self.message_user(request,"uninstall %s instances  success" %count)


admin.site.register(YigoEnv,YigoEnvAdmin)
admin.site.register(JavaEnv,JavaEnvAdmin)
admin.site.register(YigoHost,YigoHostAdmin)
admin.site.register(DatabaseHost,DatabaseHostAdmin)
admin.site.register(YigoInstance,YigoInstanceAdmin)

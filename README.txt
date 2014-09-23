# -*- mode: org; coding: utf-8 -*-
#+TITLE: README
#+AUTHOR: 陈 刚

* 介绍

  本项目是一个基于 [[http://djangoproject.com][Django]] 的 WebApp。对前台应用提供 JSON-RPC 接口，将使用 [[http://www.fabfile.org/][Fabric]] 操作远程 Linux 主机进行 YIGO 应用管理的功能提供出来。

* 配置开发环境

  1. 安装 Python，并将 Python 安装目录配置进环境变量 PATH，能在命令行环境直接运行 python 程序和 python 相关的脚本
  2. 下载 https://bootstrap.pypa.io/get-pip.py
  3. 运行 ~python get-pip.py~
  4. checkout source code
  5. ~cd yigo-runtime~
  6. Windows 系统请先安装 对应的 [[http://www.voidspace.org.uk/python/modules.shtml#pycrypto][PyCrypto]] 库
  7. 安装项目依赖的 Python 第三方库， ~pip install -r requirements.txt~

* 项目目录结构

  - key/：Fabric 需要使用的 SSH 公钥和私钥存放在此，公钥需要部署到被管理的 Linux 主机上
  - manage.py：Django 项目管理脚本
  - mc/fabtasks.py：Fabric任务都定义在此
  - mc/manager.py：JSON-RPC接口定义在此
  - mc/：Django 应用目录，此项目的程序文件都在此
  - prod.ini：生产环境 uwsgi 运行配置文件
  - requirements.txt：依赖描述文件，使用 pip 进行安装
  - templates/：修改 admin 应用页面模板的模板文件都在此
  - yigo_runtime/settings.py：此文件中除了 Django 的配置外，还有本项目使用 LOGSTASH_ 相关的配置，用于收集管理的 YIGO 应用的日志
  - yigo_runtime/：Django 项目目录，Django 相关配置文件都在此

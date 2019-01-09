from django.conf.urls import include, url
from django.contrib import admin
from taskdo.views import *

urlpatterns = [
    url(r'^adhocdo/',adhoc_task),
    url(r'^adhocdoh/',adhoc_task_h),
    url(r'^adhocdog/',adhoc_task_g),
    url(r'^adhoclog',adhoc_task_log),
    url(r'^adhocpge/',adhoc_page)
]

#!/usr/local/bin/python
from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^contact/$', views.contact, name='contact'),
    url(r'^about/$', views.about, name='about'),
    url(r'^upload/$', views.upload, name='upload'),
    url(r'^tagging/$', views.uploadText, name='tagging'),
    url(r'^skos/$', views.skos, name='skos'),
    url(r'^corpus/$', views.corpus, name='corpus'),
    url(r'^corpus_fetch/$', views.corpus_fetch, name='corpus_fetch'),
    url(r'^thesaurus/(?P<r>\w+)/$', views.uploadThesaurus, name='upload_thesaurus'),
    url(r'^reset/(?P<r>\w+)/$', views.resetThesaurus, name='reset_thesaurus'),
    url(r'^builder/$', views.builder, name='builder'),
    url(r'^scoring/$', views.scoring, name='scoring'),
    url(r'^reset_models/(?P<r>\w+)/$', views.reset_models, name='reset_models'),
    url(r'^delete_model/(?P<model>[\w\-]+)/$', views.delete_model, name='delete_model'),
    url(r'^manager/$', views.manager, name='manager'),
]

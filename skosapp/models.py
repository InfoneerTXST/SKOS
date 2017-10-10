from __future__ import unicode_literals
import os
from django.core.exceptions import ValidationError
from django.db import models
from django.forms import ModelForm

class RdfUpload(models.Model):

    title = models.CharField("<span style=\"font-weight:normal\">Title:</span>", max_length=64)
    owner = models.CharField("<span style=\"font-weight:normal\">Owner:</span>", max_length=64)
    rdf_file = models.FileField("<span style=\"font-weight:normal\">File (.rdf):</span>", upload_to="rdfs/")
    upload_date = models.DateTimeField(auto_now_add=True)
    project_ID = models.CharField("<span style=\"font-weight:normal\">Project ID:</span>", max_length=128, default=None)
    corpus_ID = models.CharField("<span style=\"font-weight:normal\">Corpus ID:</span>", max_length=128, default=None)

    def __unicode__(self):
        return str(self.upload_date)


def changed_filename_path(instance, filename):
    """
    Save the thesaurus file as <ProjectID>.rj. This keeps the folder with just
    one file per project.
    :param instance: the file submitted by the user
    :param filename:
    :return:
    """
    return os.path.join("thesaurus_data/", instance.project_ID + ".rj")


class ThesaurusUpload(models.Model):

    title = models.CharField("<span style=\"font-weight:normal\">Title:</span>", max_length=64)
    thesaurus_file = models.FileField("<span style=\"font-weight:normal\">File (.rj):</span>", upload_to=changed_filename_path)
    upload_date = models.DateTimeField(auto_now_add=True)
    project_ID = models.CharField("<span style=\"font-weight:normal\">Project ID:</span>", max_length=128, default=None)

    def __unicode__(self):
        return str(self.upload_date)


# form for uploading in corpus analyzer
class UploadForm(ModelForm):

    def clean_rdf_file(self):
        file = self.cleaned_data['rdf_file']
        filename = str(file)
        if ".rdf" not in filename:
            raise ValidationError("File is not .rdf")
        return file

    def clean_project_ID(self):
        return self.cleaned_data['project_ID']

    def clean_corpus_ID(self):
        return self.cleaned_data['corpus_ID']

    class Meta:
        model = RdfUpload
        fields = ['title', 'owner', 'project_ID', 'corpus_ID', 'rdf_file',]


# form for uploading thesaurus in entity extractor
class UploadForm2(ModelForm):

    class Meta:
        model = ThesaurusUpload
        fields = ['title', 'project_ID', 'thesaurus_file']

    def clean_thesaurus_file(self):
        file = self.cleaned_data['thesaurus_file']
        filename = str(file)
        if ".rj" not in filename:
            raise ValidationError("File is not .rj")
        return file

    def clean_project_ID(self):
        return self.cleaned_data['project_ID']

    def clean_title(self):
        return self.cleaned_data['title']

    def clean_thesaurus_filename(self):
        filename = self.cleaned_data['thesaurus_file']
        return str(filename)


class CSVUpload(models.Model):

    csv_file = models.FileField("<span style=\"font-weight:normal\">Upload CSV file. First row must be a header row (column descriptions).</span>", blank=True)

    def __unicode__(self):
        return str(self.upload_date)


# upload csv file on entity extractor page
class UploadForm3(ModelForm):

    class Meta:
        model = CSVUpload
        fields = ['csv_file']

    def clean_csv_file(self):
        file = self.cleaned_data['csv_file']
        return file

    def clean_csv_filename(self):
        filename = str(self.cleaned_data['csv_file'])
        return filename



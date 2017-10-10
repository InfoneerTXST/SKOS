import json
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponseNotAllowed
from django.core.urlresolvers import reverse, resolve
from .models import RdfUpload, UploadForm, UploadForm2, UploadForm3
from common.util.skos_tool import SkosTool
from common.util import corpus_util
import os.path
import pickle
import requests
from bs4 import BeautifulSoup
from urlparse import urljoin, urlparse
import ast
import re
import csv


def changed_filename_path(instance, filename):
    return os.path.join("thesaurus_data/", "trolol.js")


def index(request):
    return render(request, 'skosapp/home.html', {'page_title': 'Home'})


def contact(request):
    return render(request, 'skosapp/basic.html', {'page_title': 'Contact'})


def about(request):
    """
    About page currently not displayed in the header template.
    :param request: request
    :return render to display about page.
    """
    return render(request, 'skosapp/basic.html', {'page_title': 'Contact'})


def upload(request):
    """
    If POST, this view will validate and attempt to save the RDFUpload instance to the
    database. Clean corpusID and projectID from the form to get the corpus data and send
    it to corpus_util.

    If GET, serve the Upload form.
    :param request: request
    :return: if POST, send RDF to the tool for parsing and display results, otherwise, return
                a rendering of the UploadForm
    """

    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)

        if form.is_valid():
            instance = form.save(commit=False)
            # save to session for ease of use between views
            instance.save()
            request.session['rdf'] = instance.id
            project = form.clean_project_ID()
            corpus = form.clean_corpus_ID()

            corpus_util.get_corpus_data(corpus_file='corpus_data/' + corpus + '.json', corpus_id=corpus,
                                        project_id=project)

            request.session['location'] = 'corpus_data/' + corpus + '.json'
            return HttpResponseRedirect(reverse('skos'))
    else:
        form = UploadForm()

    return render(request, 'skosapp/upload.html', {'form': form,
                                                   'page_title': 'Corpus Analyzer'})


def skos(request):
    """
    View that contains
    :param request:
    :return:
    """

    pk = request.session.get('rdf', default=None)

    location = request.session['location']

    if pk:
        rdf = RdfUpload.objects.get(pk=pk)
        skos_tool = SkosTool(rdf_path=rdf.rdf_file.path)
        skos_tool.parse()
        skos_tool.get_frequencies(filename=location)
        skos_tool.sort()
        results = skos_tool.get_metrics()

        return render(request, 'skosapp/results.html', {'results': results,
                                                        'page_title': 'Corpus Analyzer'})

    else:
        # TODO template that displays the user that something went wrong
        # TODO with the processing of the rdf file
        return render(request, 'skosapp/oops.html')


def corpus(request):
    """
    view for kicking off a PoolParty sync
    :param request:
    :return:
    """
    return render(request, 'skosapp/corpus.html', {'page_title': 'Corpus Analyzer'})


def corpus_fetch(request):
    """
    executes PoolParty sync and then redirects to the upload view
    :param request:
    :return:
    """
    # corpus_util.get_corpus_data()
    return HttpResponseRedirect(reverse('upload'))


def analyze_results(request, thesaurus_dict, show_zeros, text, highlight_concepts, id, show_top, opt_text, separate_rows, rows_dict):
    try:
        if separate_rows is None:
            separate_rows = False
        if rows_dict is None:
            rows_dict = {}

        text = text.decode('windows-1252').encode('utf-8').strip()
        for key, value in rows_dict.iteritems():
            rows_dict[key] = value.decode('windows-1252').encode('utf-8').strip()

        with open('media/thesaurus_data/' + id + '.rj') as json_data:
            d = json.load(json_data)
            thesaurus = []
            myDict = {}
            top_dict = {}
            schema_dict = {}

            # <ProjectID>.rj file gets parsed
            for key, value in d.iteritems():

                if 'http://www.w3.org/2002/07/owl#deprecated' in value:
                    continue

                if 'http://www.w3.org/2000/01/rdf-schema#label' in value:
                    continue

                if 'http://www.w3.org/2004/02/skos/core#broader' not in value and not show_top:
                    continue

                if 'http://www.w3.org/2004/02/skos/core#prefLabel' in value:
                    label = value['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']
                    thesaurus.append(label)
                    myDict[label] = []

                    if 'http://www.w3.org/2004/02/skos/core#altLabel' in value:
                        for i in value['http://www.w3.org/2004/02/skos/core#altLabel']:
                            thesaurus.append(i['value'])
                            myDict[label].append(i['value'])

                    if 'http://www.w3.org/2004/02/skos/core#hiddenLabel' in value:
                        for i in value['http://www.w3.org/2004/02/skos/core#hiddenLabel']:
                            thesaurus.append(i['value'])
                            myDict[label].append(i['value'])

            for key, value in d.iteritems():

                if 'http://www.w3.org/2002/07/owl#deprecated' in value:
                    continue

                if 'http://www.w3.org/2000/01/rdf-schema#label' in value:
                    continue

                if 'http://www.w3.org/2004/02/skos/core#prefLabel' in value:
                    label = value['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']
                    top_label = ""
                    schema_label = ""

                    top_concept = key
                    while 'http://www.w3.org/2004/02/skos/core#broader' in d[top_concept] and 'http://www.w3.org/2004/02/skos/core#topConceptOf' not in d[top_concept]:
                        top_concept = d[top_concept]['http://www.w3.org/2004/02/skos/core#broader'][0]['value']

                    if 'http://www.w3.org/2004/02/skos/core#topConceptOf' in d[top_concept]:
                        schema_concept = d[top_concept]['http://www.w3.org/2004/02/skos/core#topConceptOf'][0]['value']
                        try:
                            if 'http://purl.org/dc/terms/title' in d[schema_concept]:
                                schema_label = d[schema_concept]['http://purl.org/dc/terms/title'][0]['value']
                        except Exception:
                            pass
                        if 'http://www.w3.org/2004/02/skos/core#prefLabel' in d[top_concept]:
                            top_label = d[top_concept]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']

                    top_dict[label] = top_label
                    schema_dict[label] = schema_label

        if show_zeros is None:
            show_zeros = "false"
        json_show_zeros = json.dumps(show_zeros)
        json_thesaurus = json.dumps(thesaurus)
        json_myDict = json.dumps(myDict)

        word_count_text = " " + text.replace("\t", "\n")
        while "\n" in word_count_text:
            word_count_text = word_count_text.replace("\n", " ")
        while "\r" in word_count_text:
            word_count_text = word_count_text.replace("\r", " ")
        while "  " in word_count_text:
            word_count_text = word_count_text.replace("  ", " ")
        word_count_text = word_count_text.strip()
        word_count = len(word_count_text.split(' '))

        raw_text = ' '.join(repr(word_count_text).split())
        json_raw_text = json.dumps(raw_text)

        return render(request, 'skosapp/analyze_results.html', {'json_thesaurus': json_thesaurus,
                                                                'text': text,
                                                                'json_myDict': json_myDict,
                                                                'json_raw_text': json_raw_text,
                                                                'json_text': json.dumps(text),
                                                                'json_show_zeros': json_show_zeros,
                                                                'highlight_concepts': highlight_concepts,
                                                                'page_title': 'Entity Extractor',
                                                                'word_count': word_count,
                                                                'opt_text': opt_text,
                                                                'separate': json.dumps(separate_rows),
                                                                'rows_dict': json.dumps(rows_dict),
                                                                'top_dict': json.dumps(top_dict),
                                                                'schema_dict': json.dumps(schema_dict)})

    except Exception as ex:
        return render(request, 'skosapp/wrong.html', {'page_title': 'Entity Extractor'})


def get_soup_information(r, header, footer):
    information = {}
    soup = BeautifulSoup(r.text, from_encoding=r.encoding)

    try:
        for e in soup(['style', 'script', 'head', 'img']):
            e.extract()

        for e in soup(['header']):
            if not header:
                header = True
            else:
                e.extract()

        for e in soup(['footer']):
            if not footer:
                footer = True
            else:
                e.extract()

    except Exception:
        pass

    information[0] = soup
    information[1] = header
    information[2] = footer
    information[3] = soup.get_text().replace("\t", "")

    return information


def uploadText(request):
    """
    This function gets the text from the textField and prepares the thesaurus
    that is going to use to start extracting the terms.

    The user types text in the textField and chooses a thesaurus to extract terms based on
    his/her selection. The dropdown menu contains the names of the thesaurus. Each name represent
    the value of the dictionary, and each name is associated with a key, which is the projectID.

    When user POSTs, the view gets the text and the selected thesaurus. The selected thesaurus
    has a unique ProjectID, this projectID gets searched in the list of '.rj' files. The rj file
    gets opened and parsed. All the labels are saved in two data structures, a dictionary(myDict) and a
    list(thesaurus). The dictionary contains the prefLabel as the key and the altLabels and
    hiddenLabels are the values. The list saves all the labels in a single list. This list
    will be used by the jQuery to highlight the terms and dictionary will be used to count the
    occurrences in the text.

    Before rendering, the text submitted by the user, the dictionary, and the list gets
    converted into JSON objects for the javascript processing.

    :param request:
    :return:
    """

    if os.path.exists('media/thesaurus_data/thesaurus_dict.pickle'):
        with open('media/thesaurus_data/thesaurus_dict.pickle', 'rb') as handle:
            thesaurus_dict = pickle.load(handle)

    else:
        thesaurus_dict = {}

    if request.method == 'POST' and 'tagging_submit' in request.POST:
        selected_thesaurus = request.POST.get("select_thesaurus")
        show_top = request.POST.get("show_top")
        opt_text = request.POST.get("opt_text")
        text_area = request.POST.get('text_area')
        highlight_concepts = request.POST.get('highlight_concepts')
        show_zeros = request.POST.get('show_zeros')
        depth_level = int(request.POST.get("depth_level"))
        separate_rows = request.POST.get("separate_rows")

        id = None
        for key, value in thesaurus_dict.iteritems():
            if value == selected_thesaurus:
                id = key

        if id is None:
            return render(request, 'skosapp/no_thesaurus.html', {'page_title': 'Entity Extractor'})

        if opt_text == "manual":
            if text_area == "":
                return render(request, 'skosapp/no_text.html', {'page_title': 'Entity Extractor'})

            text = text_area
            return analyze_results(request, thesaurus_dict, show_zeros, text, highlight_concepts, id, show_top, opt_text, None, None)

        elif opt_text == "csv":
            form = UploadForm3(request.POST, request.FILES)

            if form.is_valid():
                instance = form.save(commit=False)
                csv_file = form.clean_csv_file()
                csv_file_name = str(form.clean_csv_file())
                if csv_file_name[-4:] != ".csv":
                    return render(request, 'skosapp/not_csv.html', {'page_title': 'Entity Extractor'})
                text = csv_file.read()
                rows_dict = None
                if separate_rows:
                    text = ""
                    rows_dict = {}
                    reader = csv.DictReader(csv_file)
                    row_counter = 1
                    for row in reader:
                        string_row = ""
                        for k in row:
                            string_row0 = "\n" + str(k) + ":\n" + str(row[k])
                            string_row0 = string_row0.replace("\t", "\n")
                            while "\n" in string_row0:
                                string_row0 = string_row0.replace("\n", " ")
                            while "\r" in string_row0:
                                string_row0 = string_row0.replace("\r", " ")
                            while "  " in string_row0:
                                string_row0 = string_row0.replace("  ", " ")
                            string_row0 = string_row0.strip()
                            string_row0 = "\n" + string_row0
                            string_row += string_row0

                        if text == "":
                            text += "ROW " + str(row_counter) + ":\n" + string_row
                        else:
                            text += "\n\nROW " + str(row_counter) + ":\n" + string_row

                        rows_dict[row_counter] = string_row
                        row_counter += 1

                return analyze_results(request, thesaurus_dict, show_zeros, text, highlight_concepts, id, show_top, opt_text, separate_rows, rows_dict)

            return render(request, 'skosapp/not_csv.html', {'page_title': 'Entity Extractor'})

        elif opt_text == "url":
            url = text_area.strip()
            try:
                try:
                    requests.get(url)
                except Exception:
                    requests.get("http://" + url)
                if url[:11] == "http://www.":
                    pass
                elif url[:12] == "https://www.":
                    pass
                elif url[:4] == "www.":
                    url = "http://" + url
                elif url[:7] == "http://":
                    url = url[:7] + "www." + url[7:]
                elif url[:8] == "https://":
                    url = url[:8] + "www." + url[8:]
                else:
                    url = "http://www." + url
                r = requests.get(url)
            except Exception:
                return render(request, 'skosapp/invalid_url.html', {'page_title': 'Entity Extractor'})

            header = False
            footer = False

            depth_counter = 1
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(url))
            links = {url: 0}  # keys are links, values are depth level
            links_semantics = {url.replace('/', '').replace('#', ''): 0}
            links_text = {}

            information = get_soup_information(r, header, footer)
            soup = information[0]
            header = information[1]
            footer = information[2]
            links_text[url] = information[3]

            if depth_level >= 1:
                for a in soup.find_all('a'):
                    if links_semantics.get(urljoin(url, a.get('href')).replace('/', '').replace('#', '')) is None:
                        if '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(urljoin(url, a.get('href')))) == domain:
                            curr_url = urljoin(url, a.get('href'))
                            r2 = requests.get(curr_url)

                            if 'Content-Type' not in r2.headers or 'image' not in r2.headers['Content-Type'] and 'application' not in r2.headers['Content-Type'] and 'File:' not in curr_url and '.svg' not in curr_url:
                                if curr_url.rfind('#') > curr_url.rfind('/'):
                                    curr_url_split = curr_url.split('#')
                                    curr_url = curr_url_split[-2]

                                if links_semantics.get(curr_url.replace('/', '').replace('#', '')) is None:
                                    links[curr_url] = depth_counter
                                    links_semantics[curr_url.replace('/', '').replace('#', '')] = depth_counter
                                    information = get_soup_information(r2, header, footer)
                                    header = information[1]
                                    footer = information[2]
                                    links_text[curr_url] = information[3]

                depth_counter += 1

            while depth_counter <= depth_level:
                links_add = {}

                for link, depth in links.iteritems():
                    if depth == depth_counter - 1:
                        try:
                            r2 = requests.get(link)
                            information = get_soup_information(r2, header, footer)
                            soup = information[0]
                            header = information[1]
                            footer = information[2]
                            links_text[link] = information[3]

                            for a in soup.find_all('a'):
                                if links_semantics.get(urljoin(url, a.get('href')).replace('/', '').replace('#', '')) is None:
                                    if '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(urljoin(url, a.get('href')))) == domain:
                                        curr_url = urljoin(url, a.get('href'))
                                        r2 = requests.get(curr_url)

                                        if 'Content-Type' not in r2.headers or 'image' not in r2.headers['Content-Type'] and 'application' not in r2.headers['Content-Type'] and '.svg' not in curr_url:
                                            if curr_url.rfind('#') > curr_url.rfind('/'):
                                                curr_url_split = curr_url.split('#')
                                                curr_url = curr_url_split[-2]

                                            if links_semantics.get(curr_url.replace('/', '').replace('#', '')) is None:
                                                links_add[curr_url] = depth_counter
                                                links_semantics[curr_url.replace('/', '').replace('#', '')] = depth_counter
                                                information = get_soup_information(r2, header, footer)
                                                header = information[1]
                                                footer = information[2]
                                                links_text[curr_url] = information[3]

                        except Exception:
                            pass

                for link, depth in links_add.iteritems():
                    links[link] = depth

                links_add.clear()
                depth_counter += 1

            text = ""

            if depth_level == 0 or not request.POST.get("show_preview"):
                for link, depth in links.iteritems():
                    text_add = links_text[link]

                    while "\n " in text_add:
                        text_add = text_add.replace("\n ", "\n")
                    while "\n\n" in text_add:
                        text_add = text_add.replace("\n\n", "\n")
                    while "  " in text_add:
                        text_add = text_add.replace("  ", " ")

                    if text == "":
                        text += str(link) + ":\n\n" + text_add.strip()
                    else:
                        text += "\n\n\n" + str(link) + ":\n\n" + text_add.strip()

                return analyze_results(request, thesaurus_dict, show_zeros, text, highlight_concepts, id, show_top, opt_text, None, None)

            else:
                json_links = json.dumps(links)
                return render(request, 'skosapp/preview.html', {'json_links': json_links,
                                                                'links_size': len(links),
                                                                'page_title': 'Entity Extractor',
                                                                'links': json_links,
                                                                'links_text': json.dumps(links_text),
                                                                'id': json.dumps(id),
                                                                'show_top': json.dumps(show_top),
                                                                'highlight_concepts': json.dumps(highlight_concepts),
                                                                'show_zeros': json.dumps(show_zeros)})

    elif request.method == 'POST' and 'preview_submit' in request.POST:
        show_top = request.POST.get("show_top")
        links = ast.literal_eval(request.POST.get("links"))
        links_text = ast.literal_eval(request.POST.get("links_text"))
        id = request.POST.get("id")
        highlight_concepts = request.POST.get("highlight_concepts")
        show_zeros = request.POST.get("show_zeros")

        selected = False
        text = ""

        for link, depth in links.iteritems():
            if request.POST.get(link):
                selected = True

                text_add = links_text[link]

                while "\n " in text_add:
                    text_add = text_add.replace("\n ", "\n")
                while "\n\n" in text_add:
                    text_add = text_add.replace("\n\n", "\n")
                while "  " in text_add:
                    text_add = text_add.replace("  ", " ")

                if text == "":
                    text += str(link) + ":\n\n" + text_add.strip()
                else:
                    text += "\n\n\n" + str(link) + ":\n\n" + text_add.strip()

        if not selected:
            return render(request, 'skosapp/no_links.html', {'page_title': 'Entity Extractor'})

        return analyze_results(request, thesaurus_dict, show_zeros, text, highlight_concepts, id, show_top, "url", None, None)

    elif request.method == 'GET':
        form = UploadForm3()
        return render(request, 'skosapp/tagging.html', {'form': form,
                                                        'thesaurus_dict': thesaurus_dict,
                                                        'page_title': 'Entity Extractor'})

    else:
        return render(request, 'skosapp/home.html')


def uploadThesaurus(request, r):
    """
    This function handles the template where the user uploads a new thesaurus to the
    'entity extractor' tool. In order to save the thesauri saved by the user, the
    application saves a dictionary in the media/thesaurus_data folder as a pickle. This pickle
    gets loaded everytime the user opens the tagging.html template.

    All the thesauri get saved in the media/thesaurus_data folder as a <ProjectID>.rj file. Since the
    projectID is unique, only one instance of the file will exist per project.

    IF the pickle already exists, then read the pickle as a dictionary. If the thesaurus
    doesnt exists in the list of rj files, then add it to the dictionary and to the
    media/thesaurus_data folder. Otherwise, delete the existent instance of file save the
    new version in the media/thesaurus_data folder.

    If the pickle doesnt exist, create a new dictionary(keys:project_ID_field values:name_field)
    , save the new instance into the media/thesaurus_data folder and append new element to dictionary.

    :param request:
    :return: render the upload thesaurus template along with the form instance.
    """

    if r == "builder":
        page_title = "Concept Model Builder"
    elif r == "tagging":
        page_title = "Entity Extractor"
    else:
        page_title = "Thesaurus Upload"  # shouldn't ever happen

    if request.method == "POST":
        form = UploadForm2(request.POST, request.FILES)

        if form.is_valid():
            instance = form.save(commit=False)
            project_id = form.clean_project_ID()
            title = form.clean_title()

            if os.path.exists('media/thesaurus_data/thesaurus_dict.pickle'):
                with open('media/thesaurus_data/thesaurus_dict.pickle', 'rb') as handle:
                    thesaurus_dict = pickle.load(handle)

                    if project_id not in thesaurus_dict.keys() and title not in thesaurus_dict.values():
                        thesaurus_dict[project_id] = title
                        instance.save()
                        with open('media/thesaurus_data/thesaurus_dict.pickle', 'wb', ) as handle:
                            pickle.dump(thesaurus_dict, handle)

                    elif title not in thesaurus_dict.values():
                        os.remove('media/thesaurus_data/' + project_id + '.rj')
                        thesaurus_dict[project_id] = title
                        instance.save()
                        with open('media/thesaurus_data/thesaurus_dict.pickle', 'wb', ) as handle:
                            pickle.dump(thesaurus_dict, handle)

                    else:
                        return render(request, 'skosapp/thesaurus_exists.html', {'page_title': page_title})

            else:
                instance.save()
                thesaurus_dict = {}
                thesaurus_dict[project_id] = title
                with open('media/thesaurus_data/thesaurus_dict.pickle', 'wb', ) as handle:
                    pickle.dump(thesaurus_dict, handle)

            if r == "builder":
                return HttpResponseRedirect(reverse('builder'))
            elif r == "tagging":
                return HttpResponseRedirect(reverse('tagging'))
            else:
                return HttpResponseRedirect(reverse('index'))

    else:
        form = UploadForm2()
        return render(request, 'skosapp/upload_thesaurus.html', {'form': form,
                                                                 'page_title': page_title})

def resetThesaurus(request, r):
    """
    This function is called when the user wants to delete all the thesaurus in the dropdown menu.
    :param request: HTTP request
    :return: Go back to the tagging template but without the thesaurus data.
    """
    folder = 'media/thesaurus_data'

    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)

    if r == "builder":
        return HttpResponseRedirect(reverse('builder'))
    elif r == "tagging":
        return HttpResponseRedirect(reverse('tagging'))
    else:
        return HttpResponseRedirect(reverse('index'))


def builder(request):

    page_title = "Concept Model Builder"

    if os.path.exists('media/thesaurus_data/thesaurus_dict.pickle'):
        with open('media/thesaurus_data/thesaurus_dict.pickle', 'rb') as handle:
            thesaurus_dict = pickle.load(handle)

    else:
        thesaurus_dict = {}

    # POST
    if request.method == 'POST':
        concept_model = {}
        selected_thesaurus = request.POST.get("select_thesaurus")
        w_entry_pref = float(request.POST.get("entry_pref"))
        w_entry_alt = float(request.POST.get("entry_alt"))
        w_related_pref = float(request.POST.get("related_pref"))
        w_related_alt = float(request.POST.get("related_alt"))
        w_broader_pref = float(request.POST.get("broader_pref"))
        w_broader_alt = float(request.POST.get("broader_alt"))
        w_narrower_pref = float(request.POST.get("narrower_pref"))
        w_narrower_alt = float(request.POST.get("narrower_alt"))

        id = None
        for key, value in thesaurus_dict.iteritems():
            if value == selected_thesaurus:
                id = key

        if id is None:
            return render(request, 'skosapp/no_thesaurus.html', {'page_title': page_title})

        if not request.POST.get("model_title"):
            return render(request, 'skosapp/no_model_title.html', {'page_title': page_title})

        model_title = request.POST.get("model_title").strip()
        while "\n" in model_title:
            model_title = model_title.replace("\n", " ")
        while "\r" in model_title:
            model_title = model_title.replace("\r", " ")
        model_title = model_title.strip()

        with open('media/thesaurus_data/' + id + '.rj') as json_data:
            d = json.load(json_data)
            curr_id = -1

            while True:

                str_id = ""
                if curr_id >= 0:
                    str_id += str(curr_id)

                try:
                    narrowing_level = int(request.POST.get("narrowing_level" + str_id))
                    broadening_level = int(request.POST.get("broadening_level" + str_id))
                    show_related = request.POST.get("show_related" + str_id)
                    show_alt = request.POST.get("show_alt" + str_id)
                    show_top = request.POST.get("show_top" + str_id)

                    try:
                        selected_concept = request.POST.get("select_concept" + str_id).strip()

                    except Exception:
                        return render(request, 'skosapp/no_concept.html', {'page_title': page_title})

                except Exception:
                    break

                show_narrower = True
                if narrowing_level == 0:
                    show_narrower = False

                show_broader = True
                if broadening_level == 0:
                    show_broader = False

                # <ProjectID>.rj file gets parsed
                for key, concept in d.iteritems():
                    if 'http://www.w3.org/2004/02/skos/core#prefLabel' in concept:
                        if 'http://www.w3.org/2004/02/skos/core#broader' in concept or show_top:
                            if concept['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value'].strip() == selected_concept:
                                if concept_model.get(concept['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']) is None or concept_model[concept['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']] < w_entry_pref:
                                    concept_model[concept['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']] = w_entry_pref  ### weight

                                if show_alt and 'http://www.w3.org/2004/02/skos/core#altLabel' in concept:
                                    for rkey in concept['http://www.w3.org/2004/02/skos/core#altLabel']:
                                        if concept_model.get(rkey['value']) is None or concept_model[rkey['value']] < w_entry_alt:
                                            concept_model[rkey['value']] = w_entry_alt  ### weight

                                if show_related and 'http://www.w3.org/2004/02/skos/core#related' in concept:
                                    for rkey in concept['http://www.w3.org/2004/02/skos/core#related']:
                                        if 'http://www.w3.org/2004/02/skos/core#prefLabel' in d[rkey['value']]:
                                            if 'http://www.w3.org/2004/02/skos/core#broader' in d[rkey['value']] or show_top:
                                                if concept_model.get(d[rkey['value']]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']) is None or concept_model[d[rkey['value']]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']] < w_related_pref:
                                                    concept_model[d[rkey['value']]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']] = w_related_pref  ### weight

                                                if show_alt and 'http://www.w3.org/2004/02/skos/core#altLabel' in d[rkey['value']]:
                                                    for rkey_alt in d[rkey['value']]['http://www.w3.org/2004/02/skos/core#altLabel']:
                                                        if concept_model.get(rkey_alt['value']) is None or concept_model[rkey_alt['value']] < w_related_alt:
                                                            concept_model[rkey_alt['value']] = w_related_alt  ### weight

                                if show_narrower and 'http://www.w3.org/2004/02/skos/core#narrower' in concept:
                                    narrower_concepts = set()
                                    narrowing_counter = narrowing_level
                                    current_level = 1

                                    # level 1 narrowing
                                    for rkey in concept['http://www.w3.org/2004/02/skos/core#narrower']:
                                        if 'http://www.w3.org/2004/02/skos/core#prefLabel' in d[rkey['value']]:
                                            if concept_model.get(d[rkey['value']]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']) is None or concept_model[d[rkey['value']]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']] < w_narrower_pref:
                                                concept_model[d[rkey['value']]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']] = w_narrower_pref  ### weight

                                            narrower_concepts.add(rkey['value'])

                                            if show_alt and 'http://www.w3.org/2004/02/skos/core#altLabel' in d[rkey['value']]:
                                                for rkey_alt in d[rkey['value']]['http://www.w3.org/2004/02/skos/core#altLabel']:
                                                    if concept_model.get(rkey_alt['value']) is None or concept_model[rkey_alt['value']] < w_narrower_alt:
                                                        concept_model[rkey_alt['value']] = w_narrower_alt  ### weight

                                    new_narrower_concepts = set()

                                    # level 2 narrowing onwards
                                    while narrowing_counter != 1:
                                        current_level += 1

                                        for narrower_concept in narrower_concepts:
                                            if 'http://www.w3.org/2004/02/skos/core#narrower' in d[narrower_concept]:
                                                for rkey in d[narrower_concept]['http://www.w3.org/2004/02/skos/core#narrower']:
                                                    if 'http://www.w3.org/2004/02/skos/core#prefLabel' in d[rkey['value']]:
                                                        if concept_model.get(d[rkey['value']]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']) is None or concept_model[d[rkey['value']]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']] < w_narrower_pref * current_level:
                                                            concept_model[d[rkey['value']]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']] = w_narrower_pref * current_level  ### weight

                                                        new_narrower_concepts.add(rkey['value'])

                                                        if show_alt and 'http://www.w3.org/2004/02/skos/core#altLabel' in d[rkey['value']]:
                                                            for rkey_alt in d[rkey['value']]['http://www.w3.org/2004/02/skos/core#altLabel']:
                                                                if concept_model.get(rkey_alt['value']) is None or concept_model[rkey_alt['value']] < w_narrower_alt * current_level:
                                                                    concept_model[rkey_alt['value']] = w_narrower_alt * current_level  ### weight

                                        narrower_concepts.clear()

                                        for new_narrower_concept in new_narrower_concepts:
                                            narrower_concepts.add(new_narrower_concept)

                                        if narrowing_counter != 11:  # 11 is alias 'All'
                                            narrowing_counter -= 1

                                        if new_narrower_concepts.__len__() == 0:
                                            narrowing_counter = 1

                                        new_narrower_concepts.clear()

                                if show_broader and 'http://www.w3.org/2004/02/skos/core#broader' in concept:
                                    broader_concepts = set()
                                    broadening_counter = broadening_level
                                    current_level = 1

                                    # level 1 broadening
                                    for rkey in concept['http://www.w3.org/2004/02/skos/core#broader']:
                                        if 'http://www.w3.org/2004/02/skos/core#prefLabel' in d[rkey['value']]:
                                            if 'http://www.w3.org/2004/02/skos/core#broader' in d[rkey['value']] or show_top:
                                                if concept_model.get(d[rkey['value']]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']) is None or concept_model[d[rkey['value']]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']] < w_broader_pref:
                                                    concept_model[d[rkey['value']]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']] = w_broader_pref  ### weight

                                                broader_concepts.add(rkey['value'])

                                                if show_alt and 'http://www.w3.org/2004/02/skos/core#altLabel' in d[rkey['value']]:
                                                    for rkey_alt in d[rkey['value']]['http://www.w3.org/2004/02/skos/core#altLabel']:
                                                        if concept_model.get(rkey_alt['value']) is None or concept_model[rkey_alt['value']] < w_broader_alt:
                                                            concept_model[rkey_alt['value']] = w_broader_alt  ### weight

                                    new_broader_concepts = set()

                                    # level 2 broader onwards
                                    while broadening_counter != 1:
                                        current_level += 1

                                        for broader_concept in broader_concepts:
                                            if 'http://www.w3.org/2004/02/skos/core#broader' in d[broader_concept]:
                                                for rkey in d[broader_concept]['http://www.w3.org/2004/02/skos/core#broader']:
                                                    if 'http://www.w3.org/2004/02/skos/core#prefLabel' in d[rkey['value']]:
                                                        if 'http://www.w3.org/2004/02/skos/core#broader' in d[rkey['value']] or show_top:
                                                            if concept_model.get(d[rkey['value']]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']) is None or concept_model[d[rkey['value']]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']] < w_broader_pref / current_level:
                                                                concept_model[d[rkey['value']]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']] = w_broader_pref / current_level  ### weight

                                                            new_broader_concepts.add(rkey['value'])

                                                            if show_alt and 'http://www.w3.org/2004/02/skos/core#altLabel' in d[rkey['value']]:
                                                                for rkey_alt in d[rkey['value']]['http://www.w3.org/2004/02/skos/core#altLabel']:
                                                                    if concept_model.get(rkey_alt['value']) is None or concept_model[rkey_alt['value']] < w_broader_alt / current_level:
                                                                        concept_model[rkey_alt['value']] = w_broader_alt / current_level  ### weight

                                        broader_concepts.clear()

                                        for new_broader_concept in new_broader_concepts:
                                            broader_concepts.add(new_broader_concept)

                                        if broadening_counter != 11:  # 11 is alias of 'All'
                                            broadening_counter -= 1

                                        if new_broader_concepts.__len__() == 0:
                                            broadening_counter = 1

                                        new_broader_concepts.clear()

                concept_model_add = {}

                for label, weight in concept_model.iteritems():
                    if show_related:
                        for key, concept in d.iteritems():
                            if 'http://www.w3.org/2004/02/skos/core#prefLabel' in concept:
                                if concept['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value'].strip() == label.strip():
                                    if 'http://www.w3.org/2004/02/skos/core#related' in concept:
                                        for rkey in concept['http://www.w3.org/2004/02/skos/core#related']:
                                            if 'http://www.w3.org/2004/02/skos/core#prefLabel' in d[rkey['value']]:
                                                if 'http://www.w3.org/2004/02/skos/core#broader' in d[rkey['value']] or show_top:
                                                    if concept_model_add.get(d[rkey['value']]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']) is None or concept_model_add[d[rkey['value']]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']] < 1.0:
                                                        concept_model_add[d[rkey['value']]['http://www.w3.org/2004/02/skos/core#prefLabel'][0]['value']] = 1.0  ### weight

                                                    if show_alt and 'http://www.w3.org/2004/02/skos/core#altLabel' in d[rkey['value']]:
                                                        for rkey_alt in d[rkey['value']]['http://www.w3.org/2004/02/skos/core#altLabel']:
                                                            if concept_model_add.get(rkey_alt['value']) is None or concept_model_add[rkey_alt['value']] < 1.0:
                                                                concept_model_add[rkey_alt['value']] = 1.0  ### weight

                for label, weight in concept_model_add.iteritems():
                    if concept_model.get(label) is None or concept_model[label] < weight:
                        concept_model[label] = weight

                concept_model_add.clear()
                curr_id += 1

        if os.path.exists('media/model_data/model_dict.pickle'):
            with open('media/model_data/model_dict.pickle', 'rb') as handle:
                model_dict = pickle.load(handle)

                if model_title not in model_dict.keys() and model_title != "--":
                    model_dict[model_title] = concept_model
                    with open('media/model_data/model_dict.pickle', 'wb') as handle:
                        pickle.dump(model_dict, handle)

                else:
                    return render(request, 'skosapp/model_exists.html', {'page_title': page_title})

        else:
            model_dict = {}
            model_dict[model_title] = concept_model
            with open('media/model_data/model_dict.pickle', 'wb') as handle:
                pickle.dump(model_dict, handle)

        json_concept_model = json.dumps(concept_model)
        return render(request, 'skosapp/concept_model.html', {'page_title': page_title,
                                                              'model_title': model_title,
                                                              'json_concept_model': json_concept_model})

    # GET
    else:
        json_thesaurus_dict = json.dumps(thesaurus_dict)
        return render(request, 'skosapp/builder.html', {'thesaurus_dict': thesaurus_dict,
                                                        'json_thesaurus_dict': json_thesaurus_dict,
                                                        'page_title': page_title})


def find_word(w):
    return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search


def score_results(request, text, models, model_dict):
    text = text.lower()
    ratio_dict = {}

    for model in models:
        concept_counter = 0
        found_counter = 0

        for concept, weight in model_dict[model.strip()].iteritems():
            concept_counter += 1
            if find_word(concept.strip().lower())(text):
                found_counter += 1

        ratio_dict[model] = float(found_counter) / concept_counter

    word_count_text = " " + text.replace("\t", "\n")
    while "\n" in word_count_text:
        word_count_text = word_count_text.replace("\n", " ")
    while "\r" in word_count_text:
        word_count_text = word_count_text.replace("\r", " ")
    while "  " in word_count_text:
        word_count_text = word_count_text.replace("  ", " ")
    word_count_text = word_count_text.strip()
    word_count = len(word_count_text.split(' '))

    return render(request, 'skosapp/score_results.html', {'page_title': "Capability Scorer",
                                                          'word_count': word_count,
                                                          'ratio_dict': json.dumps(ratio_dict),
                                                          'json_text': json.dumps(text)})


def scoring(request):
    page_title = "Capability Scorer"

    if os.path.exists('media/model_data/model_dict.pickle'):
        with open('media/model_data/model_dict.pickle', 'rb') as handle:
            model_dict = pickle.load(handle)
    else:
        model_dict = {}

    if request.method == 'GET':
        return render(request, 'skosapp/scoring.html', {'page_title': page_title,
                                                        'model_dict': model_dict})

    elif request.method == 'POST' and 'scoring_submit' in request.POST:
        models = request.POST.getlist('models')
        text_area = request.POST.get("text_area")
        opt_text = request.POST.get("opt_text")
        depth_level = int(request.POST.get("depth_level"))

        if opt_text == "manual":
            if text_area == "":
                return render(request, 'skosapp/no_text.html', {'page_title': page_title})

            if not models:
                return render(request, 'skosapp/no_selected_model.html', {'page_title': page_title})

            text = text_area
            return score_results(request, text, models, model_dict)

        elif opt_text == "url":
            url = text_area.strip()
            try:
                try:
                    requests.get(url)
                except Exception:
                    requests.get("http://" + url)
                if url[:11] == "http://www.":
                    pass
                elif url[:12] == "https://www.":
                    pass
                elif url[:4] == "www.":
                    url = "http://" + url
                elif url[:7] == "http://":
                    url = url[:7] + "www." + url[7:]
                elif url[:8] == "https://":
                    url = url[:8] + "www." + url[8:]
                else:
                    url = "http://www." + url
                r = requests.get(url)
            except Exception:
                return render(request, 'skosapp/invalid_url.html', {'page_title': 'Entity Extractor'})

            if not models:
                return render(request, 'skosapp/no_selected_model.html', {'page_title': page_title})

            header = False
            footer = False

            depth_counter = 1
            domain = '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(url))
            links = {url: 0}  # keys are links, values are depth level
            links_semantics = {url.replace('/', '').replace('#', ''): 0}
            links_text = {}

            information = get_soup_information(r, header, footer)
            soup = information[0]
            header = information[1]
            footer = information[2]
            links_text[url] = information[3]

            if depth_level >= 1:
                for a in soup.find_all('a'):
                    if links_semantics.get(urljoin(url, a.get('href')).replace('/', '').replace('#', '')) is None:
                        if '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(urljoin(url, a.get('href')))) == domain:
                            curr_url = urljoin(url, a.get('href'))
                            r2 = requests.get(curr_url)

                            if 'Content-Type' not in r2.headers or 'image' not in r2.headers['Content-Type'] and 'application' not in r2.headers['Content-Type'] and 'File:' not in curr_url and '.svg' not in curr_url:
                                if curr_url.rfind('#') > curr_url.rfind('/'):
                                    curr_url_split = curr_url.split('#')
                                    curr_url = curr_url_split[-2]

                                if links_semantics.get(curr_url.replace('/', '').replace('#', '')) is None:
                                    links[curr_url] = depth_counter
                                    links_semantics[curr_url.replace('/', '').replace('#', '')] = depth_counter
                                    information = get_soup_information(r2, header, footer)
                                    header = information[1]
                                    footer = information[2]
                                    links_text[curr_url] = information[3]

                depth_counter += 1

            while depth_counter <= depth_level:
                links_add = {}

                for link, depth in links.iteritems():
                    if depth == depth_counter - 1:
                        try:
                            r2 = requests.get(link)
                            information = get_soup_information(r2, header, footer)
                            soup = information[0]
                            header = information[1]
                            footer = information[2]
                            links_text[link] = information[3]

                            for a in soup.find_all('a'):
                                if links_semantics.get(urljoin(url, a.get('href')).replace('/', '').replace('#', '')) is None:
                                    if '{uri.scheme}://{uri.netloc}/'.format(uri=urlparse(urljoin(url, a.get('href')))) == domain:
                                        curr_url = urljoin(url, a.get('href'))
                                        r2 = requests.get(curr_url)

                                        if 'Content-Type' not in r2.headers or 'image' not in r2.headers['Content-Type'] and 'application' not in r2.headers['Content-Type'] and '.svg' not in curr_url:
                                            if curr_url.rfind('#') > curr_url.rfind('/'):
                                                curr_url_split = curr_url.split('#')
                                                curr_url = curr_url_split[-2]

                                            if links_semantics.get(curr_url.replace('/', '').replace('#', '')) is None:
                                                links_add[curr_url] = depth_counter
                                                links_semantics[curr_url.replace('/', '').replace('#', '')] = depth_counter
                                                information = get_soup_information(r2, header, footer)
                                                header = information[1]
                                                footer = information[2]
                                                links_text[curr_url] = information[3]

                        except Exception:
                            pass

                for link, depth in links_add.iteritems():
                    links[link] = depth

                links_add.clear()
                depth_counter += 1

            text = ""

            if depth_level == 0 or not request.POST.get("show_preview"):
                for link, depth in links.iteritems():
                    text_add = links_text[link]

                    while "\n " in text_add:
                        text_add = text_add.replace("\n ", "\n")
                    while "\n\n" in text_add:
                        text_add = text_add.replace("\n\n", "\n")
                    while "  " in text_add:
                        text_add = text_add.replace("  ", " ")

                    if text == "":
                        text += str(link) + ":\n\n" + text_add.strip()
                    else:
                        text += "\n\n\n" + str(link) + ":\n\n" + text_add.strip()

                return score_results(request, text, models, model_dict)

            else:
                json_links = json.dumps(links)
                return render(request, 'skosapp/preview2.html', {'json_links': json_links,
                                                                 'links_size': len(links),
                                                                 'page_title': 'Entity Extractor',
                                                                 'links': json_links,  # from here down -> secret parameters
                                                                 'links_text': json.dumps(links_text),
                                                                 'models': json.dumps(models)})

    elif request.method == 'POST' and 'preview_submit' in request.POST:
        links = ast.literal_eval(request.POST.get("links"))
        links_text = ast.literal_eval(request.POST.get("links_text"))
        models = ast.literal_eval(request.POST.get("models"))

        selected = False
        text = ""

        for link, depth in links.iteritems():
            if request.POST.get(link):
                selected = True

                text_add = links_text[link]

                while "\n " in text_add:
                    text_add = text_add.replace("\n ", "\n")
                while "\n\n" in text_add:
                    text_add = text_add.replace("\n\n", "\n")
                while "  " in text_add:
                    text_add = text_add.replace("  ", " ")

                if text == "":
                    text += str(link) + ":\n\n" + text_add.strip()
                else:
                    text += "\n\n\n" + str(link) + ":\n\n" + text_add.strip()

        if not selected:
            return render(request, 'skosapp/no_links.html', {'page_title': 'Entity Extractor'})

        return score_results(request, text, models, model_dict)


def reset_models(request, r):
    folder = 'media/model_data'

    for the_file in os.listdir(folder):
        file_path = os.path.join(folder, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(e)

    if r == "manager":
        return HttpResponseRedirect(reverse('manager'))
    else:
        return HttpResponseRedirect(reverse('index'))


def delete_model(request, model):
    model = model.replace("30389538919375365300003959385937367", " ")
    model_dict = {}

    if os.path.exists('media/model_data/model_dict.pickle'):
        with open('media/model_data/model_dict.pickle', 'rb') as handle:
            model_dict = pickle.load(handle)

        model_dict.pop(model, None)

        with open('media/model_data/model_dict.pickle', 'wb') as handle:
            pickle.dump(model_dict, handle)

    if not model_dict:
        folder = 'media/model_data'
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)

    return HttpResponseRedirect(reverse('manager'))


def manager(request):
    page_title = "Concept Model Manager"

    if os.path.exists('media/model_data/model_dict.pickle'):
        with open('media/model_data/model_dict.pickle', 'rb') as handle:
            model_dict = pickle.load(handle)
    else:
        model_dict = {}

    if os.path.exists('media/thesaurus_data/thesaurus_dict.pickle'):
        with open('media/thesaurus_data/thesaurus_dict.pickle', 'rb') as handle:
            thesaurus_dict = pickle.load(handle)
    else:
        thesaurus_dict = {}

    if request.method == 'GET':
        return render(request, 'skosapp/manager.html', {'page_title': page_title,
                                                        'model_dict': model_dict,
                                                        'thesaurus_dict': thesaurus_dict,
                                                        'json_model_dict': json.dumps(model_dict),
                                                        'json_thesaurus_dict': json.dumps(thesaurus_dict)})

    elif request.method == 'POST':
        model = request.POST.get("model_list")
        new_dict = ast.literal_eval(request.POST.get("new_dict"))
        for concept, weight in new_dict.iteritems():
            try:
                new_dict[concept] = float(weight)
            except Exception:
                return render(request, 'skosapp/invalid_weight.html', {'page_title': page_title})

        model_dict[model] = new_dict

        if os.path.exists('media/model_data/model_dict.pickle'):
            with open('media/model_data/model_dict.pickle', 'wb') as handle:
                pickle.dump(model_dict, handle)

        return render(request, 'skosapp/manager.html', {'page_title': page_title,
                                                        'model_dict': model_dict,
                                                        'thesaurus_dict': thesaurus_dict,
                                                        'json_model_dict': json.dumps(model_dict),
                                                        'json_thesaurus_dict': json.dumps(thesaurus_dict)})

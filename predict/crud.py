from crudbuilder.abstract import BaseCrudBuilder

from predict.models import Prediction, Person


class PredictionCrud(BaseCrudBuilder):
    model = Prediction
    search_fields = ['text']
    tables2_fields = ('text')
    tables2_css_class = "table table-bordered table-condensed"
    tables2_pagination = 20  # default is 10
    modelform_excludes = []
    login_required = False
    permission_required = False
    # permissions = {
    #   'list': 'example.person_list',
    #       'create': 'example.person_create'
    # }


class PersonCrud(BaseCrudBuilder):
    model = Person
    search_fields = ['name']
    tables2_fields = ('name', 'email')
    tables2_css_class = "table table-bordered table-condensed"
    tables2_pagination = 20  # default is 10
    modelform_excludes = []
    login_required = False
    permission_required = False
    # permissions = {
    #   'list': 'example.person_list',
    #       'create': 'example.person_create'
    # }

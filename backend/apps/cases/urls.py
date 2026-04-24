from django.urls import re_path

from apps.cases.views import (
    CaseGenerateView,
    CaseListCreateView,
    CaseRetrieveDeleteView,
    CaseSaveView,
    NoteParseUploadView,
)

app_name = "cases"

## regex urls design
urlpatterns = [
    re_path(r"^cases/?$", CaseListCreateView.as_view(), name="case-list-create"),
    re_path(r"^cases/(?P<pk>\d+)/?$", CaseRetrieveDeleteView.as_view(), name="case-detail"),
    re_path(
        r"^cases/(?P<pk>\d+)/generate/?$",
        CaseGenerateView.as_view(),
        name="case-generate",
    ),
    re_path(
        r"^cases/(?P<pk>\d+)/save/?$",
        CaseSaveView.as_view(),
        name="case-save",
    ),
    re_path(
        r"^uploads/parse-note/?$",
        NoteParseUploadView.as_view(),
        name="parse-note-upload",
    ),
]

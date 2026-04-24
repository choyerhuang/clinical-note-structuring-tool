from django.urls import path

from apps.cases.views import (
    CaseGenerateView,
    CaseListCreateView,
    CaseRetrieveDeleteView,
    CaseSaveView,
    NoteParseUploadView,
)

app_name = "cases"

urlpatterns = [
    path("cases/", CaseListCreateView.as_view(), name="case-list-create"),
    path("cases/<int:pk>/", CaseRetrieveDeleteView.as_view(), name="case-detail"),
    path("cases/<int:pk>/generate/", CaseGenerateView.as_view(), name="case-generate"),
    path("cases/<int:pk>/save/", CaseSaveView.as_view(), name="case-save"),
    path("uploads/parse-note/", NoteParseUploadView.as_view(), name="parse-note-upload"),
]

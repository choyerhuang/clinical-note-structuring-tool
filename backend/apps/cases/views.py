from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cases.models import Case, CaseStatus, EditedResult, GeneratedResult
from apps.cases.serializers import (
    CaseSerializer,
    EditedResultSaveSerializer,
    NoteParseUploadSerializer,
)
from apps.cases.services.llm_client import LLMServiceError
from apps.cases.services.pipeline import run_generate_pipeline
from apps.cases.services.file_parsing import parse_uploaded_note_file

## Get all cases or Generate new Case
class CaseListCreateView(generics.ListCreateAPIView):
    queryset = Case.objects.select_related("generated_result", "edited_result").all()
    serializer_class = CaseSerializer

## Handle single case
class CaseRetrieveView(generics.RetrieveAPIView):
    queryset = Case.objects.select_related("generated_result", "edited_result").all()
    serializer_class = CaseSerializer

## Handle single case get and delete
class CaseRetrieveDeleteView(generics.RetrieveDestroyAPIView):
    queryset = Case.objects.select_related("generated_result", "edited_result").all()
    serializer_class = CaseSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({"success": True}, status=status.HTTP_200_OK)


## LLM Generate calling
class CaseGenerateView(APIView):
    def post(self, request, pk):
        case = get_object_or_404(
            Case.objects.select_related("generated_result", "edited_result"),
            pk=pk,
        )

        try:
            pipeline_result = run_generate_pipeline(case.original_note) 
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        except LLMServiceError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        structured_output = pipeline_result["structured_output"]
        mcg_result = pipeline_result["mcg_result"]
        revised_hpi = pipeline_result["revised_hpi"]
        generation_warnings = pipeline_result["warnings"]
        generation_warning_groups = pipeline_result["warning_groups"]
        verification = pipeline_result["verification"]
        confidence_result = pipeline_result["confidence_result"]

        generated_defaults = {
            "chief_complaint_generated": structured_output["chief_complaint_generated"],
            "hpi_summary_generated": structured_output["hpi_summary_generated"],
            "key_findings_generated": structured_output["key_findings_generated"],
            "suspected_conditions_generated": structured_output[
                "suspected_conditions_generated"
            ],
            "disposition_generated": structured_output["disposition_generated"],
            "uncertainties_generated": structured_output["uncertainties_generated"],
            "revised_hpi_generated": revised_hpi,
            "generation_warnings": generation_warnings,
            "verification_result": verification,
            "mcg_result": mcg_result,
            "confidence_result": confidence_result,
        }

        with transaction.atomic():
            GeneratedResult.objects.update_or_create(
                case=case,
                defaults=generated_defaults,
            )
            case.status = CaseStatus.GENERATED
            case.latest_disposition = structured_output["disposition_generated"]
            case.save(update_fields=["status", "latest_disposition", "updated_at"])

        case.refresh_from_db()
        serialized_case = CaseSerializer(case)
        response_data = {
            **serialized_case.data,
            "mcg_result": mcg_result,
            "generation_warnings": generation_warnings,
            "generation_warning_groups": generation_warning_groups,
            "verification": verification,
            "confidence_result": confidence_result,
        }
        return Response(response_data, status=status.HTTP_200_OK)

## Human-in-loop design check difference between difference and edited, saved in Database
class CaseSaveView(APIView):
    def put(self, request, pk):
        case = get_object_or_404(
            Case.objects.select_related("generated_result", "edited_result"),
            pk=pk,
        )
        serializer = EditedResultSaveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        validated_data = serializer.validated_data
        generated_result = getattr(case, "generated_result", None)

        generated_field_map = {
            "chief_complaint_final": (
                getattr(generated_result, "chief_complaint_generated", "")
                if generated_result
                else ""
            ),
            "hpi_summary_final": (
                getattr(generated_result, "hpi_summary_generated", "")
                if generated_result
                else ""
            ),
            "key_findings_final": (
                getattr(generated_result, "key_findings_generated", [])
                if generated_result
                else []
            ),
            "suspected_conditions_final": (
                getattr(generated_result, "suspected_conditions_generated", [])
                if generated_result
                else []
            ),
            "disposition_final": (
                getattr(generated_result, "disposition_generated", "Unknown")
                if generated_result
                else "Unknown"
            ),
            "uncertainties_final": (
                getattr(generated_result, "uncertainties_generated", [])
                if generated_result
                else []
            ),
            "revised_hpi_final": (
                getattr(generated_result, "revised_hpi_generated", "")
                if generated_result
                else ""
            ),
        }

        edited_fields = [
            field_name
            for field_name, field_value in validated_data.items()
            if field_value != generated_field_map.get(field_name)
        ]

        edited_result_defaults = {
            **validated_data,
            "edited_fields": edited_fields,
        }

        with transaction.atomic():
            EditedResult.objects.update_or_create(
                case=case,
                defaults=edited_result_defaults,
            )
            case.has_user_edits = True
            case.latest_disposition = validated_data["disposition_final"]
            case.status = CaseStatus.SAVED
            case.save(
                update_fields=[
                    "has_user_edits",
                    "latest_disposition",
                    "status",
                    "updated_at",
                ]
            )

        case.refresh_from_db()
        serialized_case = CaseSerializer(case)
        return Response(serialized_case.data, status=status.HTTP_200_OK)


class NoteParseUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = NoteParseUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        parse_result = parse_uploaded_note_file(serializer.validated_data["file"])
        response_status = (
            status.HTTP_200_OK if parse_result["success"] else status.HTTP_400_BAD_REQUEST
        )
        return Response(parse_result, status=response_status)

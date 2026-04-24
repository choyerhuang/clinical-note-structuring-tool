from rest_framework import serializers

from apps.cases.models import Case, Disposition, EditedResult, GeneratedResult


class GeneratedResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedResult
        fields = [
            "id",
            "chief_complaint_generated",
            "hpi_summary_generated",
            "key_findings_generated",
            "suspected_conditions_generated",
            "disposition_generated",
            "uncertainties_generated",
            "revised_hpi_generated",
            "generation_warnings",
            "verification_result",
            "mcg_result",
            "confidence_result",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class EditedResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = EditedResult
        fields = [
            "id",
            "chief_complaint_final",
            "hpi_summary_final",
            "key_findings_final",
            "suspected_conditions_final",
            "disposition_final",
            "uncertainties_final",
            "revised_hpi_final",
            "edited_fields",
            "last_edited_at",
        ]
        read_only_fields = fields


class CaseSerializer(serializers.ModelSerializer):
    generated_result = GeneratedResultSerializer(read_only=True)
    edited_result = EditedResultSerializer(read_only=True)

    class Meta:
        model = Case
        fields = [
            "id",
            "title",
            "original_note",
            "status",
            "latest_disposition",
            "has_user_edits",
            "created_at",
            "updated_at",
            "generated_result",
            "edited_result",
        ]
        read_only_fields = [
            "id",
            "status",
            "latest_disposition",
            "has_user_edits",
            "created_at",
            "updated_at",
            "generated_result",
            "edited_result",
        ]


class EditedResultSaveSerializer(serializers.Serializer):
    chief_complaint_final = serializers.CharField(allow_blank=True)
    hpi_summary_final = serializers.CharField(allow_blank=True)
    key_findings_final = serializers.ListField(
        child=serializers.CharField(allow_blank=False),
    )
    suspected_conditions_final = serializers.ListField(
        child=serializers.CharField(allow_blank=False),
    )
    disposition_final = serializers.ChoiceField(choices=Disposition.choices)
    uncertainties_final = serializers.ListField(
        child=serializers.CharField(allow_blank=False),
    )
    revised_hpi_final = serializers.CharField(allow_blank=True)

    def validate_key_findings_final(self, value):
        return [item.strip() for item in value if item.strip()]

    def validate_suspected_conditions_final(self, value):
        return [item.strip() for item in value if item.strip()]

    def validate_uncertainties_final(self, value):
        return [item.strip() for item in value if item.strip()]


class NoteParseUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    note_type = serializers.ChoiceField(
        choices=[("er", "ER"), ("hp", "H&P")],
        required=False,
        allow_null=True,
    )

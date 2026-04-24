from django.db import models


class CaseStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    GENERATED = "generated", "Generated"
    SAVED = "saved", "Saved"


class Disposition(models.TextChoices):
    ADMIT = "Admit", "Admit"
    OBSERVE = "Observe", "Observe"
    DISCHARGE = "Discharge", "Discharge"
    UNKNOWN = "Unknown", "Unknown"


class Case(models.Model):
    title = models.CharField(max_length=255)
    original_note = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=CaseStatus.choices,
        default=CaseStatus.DRAFT,
    )
    latest_disposition = models.CharField(
        max_length=20,
        choices=Disposition.choices,
        null=True,
        blank=True,
    )
    has_user_edits = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-created_at"]

    def __str__(self):
        return f"Case #{self.pk or 'new'}: {self.title}"


class GeneratedResult(models.Model):
    case = models.OneToOneField(
        Case,
        related_name="generated_result",
        on_delete=models.CASCADE,
    )
    chief_complaint_generated = models.TextField(blank=True)
    hpi_summary_generated = models.TextField(blank=True)
    key_findings_generated = models.JSONField(default=list, blank=True)
    suspected_conditions_generated = models.JSONField(default=list, blank=True)
    disposition_generated = models.CharField(
        max_length=20,
        choices=Disposition.choices,
        default=Disposition.UNKNOWN,
    )
    uncertainties_generated = models.JSONField(default=list, blank=True)
    revised_hpi_generated = models.TextField(blank=True)
    generation_warnings = models.JSONField(default=list, blank=True)
    verification_result = models.JSONField(null=True, blank=True)
    mcg_result = models.JSONField(null=True, blank=True)
    confidence_result = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Generated result"
        verbose_name_plural = "Generated results"

    def __str__(self):
        return f"Generated result for case #{self.case_id}"


class EditedResult(models.Model):
    case = models.OneToOneField(
        Case,
        related_name="edited_result",
        on_delete=models.CASCADE,
    )
    chief_complaint_final = models.TextField(blank=True)
    hpi_summary_final = models.TextField(blank=True)
    key_findings_final = models.JSONField(default=list, blank=True)
    suspected_conditions_final = models.JSONField(default=list, blank=True)
    disposition_final = models.CharField(
        max_length=20,
        choices=Disposition.choices,
        default=Disposition.UNKNOWN,
    )
    uncertainties_final = models.JSONField(default=list, blank=True)
    revised_hpi_final = models.TextField(blank=True)
    edited_fields = models.JSONField(default=list, blank=True)
    last_edited_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Edited result"
        verbose_name_plural = "Edited results"

    def __str__(self):
        return f"Edited result for case #{self.case_id}"

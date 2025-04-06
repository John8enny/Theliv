from django import forms
from .models import Evidence
from django.contrib.auth.models import User

class EvidenceForm(forms.ModelForm):
    class Meta:
        model = Evidence
        fields = ['evd_name', 'case_num', 'description', 'file_type', 'custom_data']

    file = forms.FileField(required=True)

    # Read-only fields to display generated values
    evd_id = forms.CharField(required=False, disabled=True)
    cid = forms.CharField(required=False, disabled=True)
    file_hash = forms.CharField(required=False, disabled=True)
    metadata = forms.JSONField(required=False, disabled=True)

class SearchForm(forms.Form):
    evidence_number = forms.CharField(required=False, label="Search by Evidence Number")
    case_number = forms.CharField(required=False, label="Search by Case Number")

class TransferForm(SearchForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize recipient field to show organization tags
        self.fields['recipient'].queryset = User.objects.all()
        self.fields['recipient'].label_from_instance = self.label_from_instance

    @staticmethod
    def label_from_instance(obj):
        # Get user's groups (organizations) and join them with username
        groups = obj.groups.all()
        org_tag = f" [{', '.join(group.name for group in groups)}]" if groups else " [No Organization]"
        return f"{obj.username}{org_tag}"

    recipient = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label="Transfer to",
        empty_label="Select Recipient"
    )
from django import forms
from cyder.cydhcp.interface.dynamic_intr.models import (DynamicInterface,
                                                        DynamicIntrKeyValue)
from cyder.base.mixins import UsabilityFormMixin
from cyder.cydhcp.forms import RangeWizard


class DynamicInterfaceForm(RangeWizard, UsabilityFormMixin):

    def __init__(self, *args, **kwargs):
        super(DynamicInterfaceForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['system', 'mac', 'vrf', 'site',
                                'range', 'workgroup', 'dhcp_enabled', 'ctnr']
        self.fields['range'].required = True

    class Meta:
        model = DynamicInterface
        exclude = ('last_seen')


class DynamicIntrKeyValueForm(forms.ModelForm):
    dynamic_interface = forms.ModelChoiceField(
        queryset=DynamicInterface.objects.all(),
        widget=forms.HiddenInput())

    class Meta:
        model = DynamicIntrKeyValue
        exclude = ('is_option', 'is_statement', 'is_quoted',)

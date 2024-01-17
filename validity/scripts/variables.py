from extras.scripts import ChoiceVar

from validity.forms.helpers import IntegerChoiceField


class NoNullChoiceVar(ChoiceVar):
    def __init__(self, choices, *args, **kwargs):
        super().__init__(choices, *args, **kwargs)
        self.field_attrs["choices"] = choices


class VerbosityVar(NoNullChoiceVar):
    form_field = IntegerChoiceField

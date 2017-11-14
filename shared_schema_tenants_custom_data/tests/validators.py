from django.core.exceptions import ValidationError
from django.utils.text import ugettext_lazy as _


def validator_gt_2(value):
    if int(value) <= 2:
        raise ValidationError(_("This field must be a valid integer"))

    return int(value)


def validator_lt_2(value):
    if int(value) >= 2:
        raise ValidationError(_("This field must be a valid integer"))

    return int(value)

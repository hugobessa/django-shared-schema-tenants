import json


def validate_json(value):
    try:
        value = json.loads(value)
    except json.decoder.JSONDecodeError:
        raise ValidationError(_("This field must be a valid json"))
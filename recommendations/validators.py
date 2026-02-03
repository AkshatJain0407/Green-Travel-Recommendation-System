from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re


class ComplexityValidator:
    """Validate whether the password contains at least one uppercase letter,
    one lowercase letter, one digit and one special character.
    """

    def validate(self, password, user=None):
        if not password:
            return

        errors = []
        if not re.search(r"[A-Z]", password):
            errors.append(_('Password must contain at least one uppercase letter.'))
        if not re.search(r"[a-z]", password):
            errors.append(_('Password must contain at least one lowercase letter.'))
        if not re.search(r"\d", password):
            errors.append(_('Password must contain at least one digit.'))
        if not re.search(r"[^A-Za-z0-9]", password):
            errors.append(_('Password must contain at least one special character (e.g. !@#$%).'))

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Your password must contain at least one uppercase letter, one lowercase letter, "
            "one digit and one special character."
        )

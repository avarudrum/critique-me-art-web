from django import forms


class NoLabelSuffixMixin:
    """Drops Django's default ':' after every label.

    The labels are styled as letterspaced small caps, and letter-spacing adds a
    gap before the colon, so "TITLE :" reads as a mistake.

    Passed through __init__ rather than set as a class attribute: BaseForm
    assigns `self.label_suffix` in its own __init__, so a class attribute would
    simply be overwritten. setdefault leaves an explicit caller in control.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super().__init__(*args, **kwargs)

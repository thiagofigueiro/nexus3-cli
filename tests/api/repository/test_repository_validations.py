import pytest

from nexuscli.api.repository import validations


@pytest.mark.parametrize('value, known, x_exception', [
    # value         known                     x_exception
    ('value',       [],                       True),
    ('value',       ['value'],                False),
    ('other value', ['value'],                True),
    ('other value', ['value', 'other value'], False),
])
def test_ensure_known(value, known, x_exception):
    if x_exception:
        with pytest.raises(ValueError):
            validations.ensure_known('target', value, known)
    else:
        validations.ensure_known('target', value, known)

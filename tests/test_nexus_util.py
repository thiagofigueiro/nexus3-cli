# -*- coding: utf-8 -*-
import pytest

from nexuscli.nexus_util import filtered_list_gen


@pytest.mark.parametrize('artefact_path,x_count', [
    (None,              0),
    (['not a string'],  0),
    (999,               0),
    ('some path',       1),
])
def test_filtered_list_gen(artefact_path, x_count):
    raw_response = [{'path': artefact_path}]

    filtered_artefacts = filtered_list_gen(raw_response)

    assert x_count == sum(1 for _ in filtered_artefacts)


@pytest.mark.parametrize('artefact_path, starts_with, x_count', [
    ('some path/',          '',           1),
    ('some path/some file', '',           1),
    ('some path/',          'some ',      1),
    ('some path/',          'some path',  1),
    ('some path/',          'some path/', 1),
    ('some path/some file', 'some file',  0),
    ('some path', 'path',                 0),
    ('👌 ugh tf', '👌',                    1),
    ('😝',        '👌',                    0),
])
def test_filtered_list_gen_starts_with(
        artefact_path, starts_with, x_count):
    raw_response = [{'path': artefact_path}]

    filtered_artefacts = filtered_list_gen(raw_response, starts_with)

    assert x_count == sum(1 for _ in filtered_artefacts)

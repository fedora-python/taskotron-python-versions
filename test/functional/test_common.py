import pytest

from taskotron_python_versions.common import file_contains

from .common import gpkg_path


@pytest.mark.parametrize('thing', ('Whither Canada?',
                                   'Sex and Violence',
                                   'Owl Stretching Time',
                                   'Full Frontal Nudity'))
def test_this_file_contains_things_it_does(thing):
    # given the nature of this test, just specifying the parameters makes
    # the file contain them (mindblown!)
    assert file_contains(__file__, thing)


@pytest.mark.parametrize('thing', ('How to Recognise Different Types of Trees'
                                   ' From Quite a Long Way Away',
                                   'Man\'s Crisis of Identity in the Latter'
                                   ' Half of the 20th Century',
                                   'You\'re No Fun Anymore'))
def test_this_file_doesnt_contain_things_it_doesnt(thing):
    # given the nature of this test, all the things have to be a bit obfuscated
    assert not file_contains(__file__, thing)


@pytest.mark.parametrize(('word', 'is_in'), (('python', True),
                                             ('abracadabra', False)))
def test_searching_in_weird_logs(word, is_in):
    fake_log = gpkg_path('yum*')
    assert file_contains(fake_log, word) == is_in

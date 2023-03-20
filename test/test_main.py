import pytest
import pyEM as em

@pytest.fixture(scope='module')
def navlines():
    return em.loadtext('./test_files/sort.nav')

@pytest.fixture(scope='module')
def navlines_xml():
    return em.loadtext('./test_files/sort_xml.nav')


def test_loadtext():

    with pytest.raises(FileNotFoundError):
        em.loadtext('./thisfiledoesnotextist.nav')

    inlist = em.loadtext('./test_files/sort.nav')

    assert len(inlist) == 140

    assert inlist[14] == 'FitToPolygonID = 0'
    assert inlist[99] == 'GroupID = 1074138545'


def test_nav_item(navlines, navlines_xml, capsys):

    for xml,navl in enumerate([navlines_xml, navlines]):
        # check if empty line at EOF
        if navl[-1] != '':
            navl = navl + ['']

        assert em.nav_item(navl, 'nonexistingitem') == ([], navl)

        captured = capsys.readouterr()
        assert 'ERROR: Navigator Item ' in captured.out

        item0, out0 = em.nav_item(navl, '000')

        assert type(item0) is dict
        assert 'StageXYZ' in item0.keys()

        assert all(line in navl[1:] for line in out0[1:-1])

        if xml > 0:
            assert '<Item name="' + item0['# Item'] + '">' not in out0
            assert '<PtsX>' + item0['PtsX'][0] + '</PtsX>' not in out0
        else:
            assert '[Item = ' + item0['# Item'] + ']' not in out0
            assert 'PtsX = ' + item0['PtsX'][0] not in out0










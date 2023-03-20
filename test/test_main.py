import os.path
import pytest
import shutil

import pyEM as em

from test_data import example_map

@pytest.fixture(scope='module')
def navlines():
    return em.loadtext('./test_files/sort.nav')


@pytest.fixture(scope='module')
def navlines_xml():
    return em.loadtext('./test_files/sort_xml.nav')

@pytest.fixture(scope='module')
def mapitem(navlines):
    return em.nav_item(navlines, '12-A')[0]

def test_loadtext():
    with pytest.raises(FileNotFoundError):
        em.loadtext('./thisfiledoesnotextist.nav')

    inlist = em.loadtext('./test_files/sort.nav')

    assert len(inlist) == 140

    assert inlist[14] == 'FitToPolygonID = 0'
    assert inlist[99] == 'GroupID = 1074138545'


def test_nav_item(navlines, navlines_xml, capsys):
    for xml, navl in enumerate([navlines_xml, navlines]):
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


def test_mdoc_item(navlines, mapitem, capsys):
    # check if empty line at EOF
    if navlines[-1] != '':
        navlines += ['']

    assert em.mdoc_item(navlines, '12-A') == {}

    captured = capsys.readouterr()
    assert 'ERROR: Item ' in captured.out

    item0 = em.mdoc_item(navlines, 'Item = 12-A')

    mapitem.pop('# Item')
    assert mapitem == item0

    expectedheader = {'AdocVersion': ['2.00'], 'LastSavedAs': ['pyem\\test\\test_files\\sort.nav']}
    assert em.mdoc_item(navlines, '', header=True) == expectedheader


def test_parse_adoc(navlines):
    testlines = navlines[:2]

    dict0 = em.parse_adoc(testlines)

    assert dict0 == em.mdoc_item(navlines, '', header=True)


def test_map_file(mapitem):
    mapitem0 = dict(mapitem)

    mapitem0['MapFile']=['Filethatclearlydoesnotexist.nonono']

    with pytest.raises(FileNotFoundError):
        em.map_file(mapitem0)

    mapfile0 = em.map_file(mapitem)

    assert mapfile0 == example_map
    assert os.path.exists(mapfile0)
    assert os.path.relpath(mapfile0,os.getcwd()) == 'test_files/MMM_01.mrc'

    # test in local folder

    shutil.copy(mapfile0,'.')
    mapfile1 = em.map_file(mapitem)

    assert mapfile1 == 'MMM_01.mrc'
    os.remove(mapfile1)
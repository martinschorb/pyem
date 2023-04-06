import os.path
import pytest
import shutil
import numpy as np

from skimage.io import imread

import pyEM as em

from test_data import example_map, expected


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
    for xml, navl in enumerate([navlines, navlines_xml]):
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


def test_adoc_item(navlines, mapitem, capsys):
    # check if empty line at EOF
    if navlines[-1] != '':
        navlines += ['']

    assert em.adoc_items(navlines, 'nonexistingstring') == []

    captured = capsys.readouterr()
    assert 'ERROR: String ' in captured.out

    assert em.adoc_items(navlines, '000499') == []

    captured = capsys.readouterr()
    assert 'not found in labels!' in captured.out

    item0 = em.adoc_items(navlines, 'Item = 12-A')[0]

    assert '# [Item = 12-A]' in item0.keys()

    mapitem0 = dict(mapitem)

    assert item0['# [Item = 12-A]'] == mapitem0['# Item']

    mapitem0.pop('# Item')
    item0.pop('# [Item = 12-A]')

    assert mapitem0 == item0

    expectedheader = {'AdocVersion': ['2.00'], 'LastSavedAs': ['pyem\\test\\test_files\\sort.nav']}
    assert em.adoc_items(navlines, '', header=True) == [expectedheader]


def test_mdoc_item(navlines, mapitem, capsys):
    # check if empty line at EOF
    if navlines[-1] != '':
        navlines += ['']

    assert em.mdoc_item(navlines, '12-A') == {}

    captured = capsys.readouterr()
    assert 'ERROR: Item ' in captured.out

    item0 = em.mdoc_item(navlines, 'Item = 12-A')

    mapitem0 = dict(mapitem)

    mapitem0.pop('# Item')
    assert mapitem0 == item0

    expectedheader = {'AdocVersion': ['2.00'], 'LastSavedAs': ['pyem\\test\\test_files\\sort.nav']}
    assert em.mdoc_item(navlines, '', header=True) == expectedheader


def test_parse_adoc(navlines):
    testlines = navlines[:2]

    dict0 = em.parse_adoc(testlines)

    assert dict0 == em.mdoc_item(navlines, '', header=True)


def test_map_file(mapitem):
    mapitem0 = dict(mapitem)

    mapitem0['MapFile'] = ['Filethatclearlydoesnotexist.nonono']

    with pytest.raises(FileNotFoundError):
        em.map_file(mapitem0)

    mapfile0 = em.map_file(mapitem)

    assert mapfile0 == example_map
    assert os.path.exists(mapfile0)
    assert os.path.relpath(mapfile0, os.getcwd()) == 'test_files/MMM_01.mrc'

    # test in local folder

    shutil.copy(mapfile0, '.')
    mapfile1 = em.map_file(mapitem)

    assert mapfile1 == 'MMM_01.mrc'
    os.remove(mapfile1)

    # test in sub-sub-sub-folder
    testdir = 'd1/d2/d3'
    os.makedirs(testdir)
    shutil.move(mapfile0, testdir)

    mapfile2 = em.map_file(mapitem)

    assert os.path.relpath(mapfile2, os.getcwd()) == testdir + '/MMM_01.mrc'
    shutil.move(mapfile2, mapfile0)
    shutil.rmtree('d1')


def test_map_header(mapitem):
    assert em.map_header('nonexistingmap') == {}

    # file name as string or from a map nav-dict
    for header in (em.map_header(example_map), em.map_header(mapitem)):

        assert type(header) is dict
        for key in ('xsize', 'ysize', 'stacksize', 'pixelsize'):
            assert key in header.keys()
            assert header['xsize'] == 1852
            assert header['stacksize'] == 4


def test_itemtonav(mapitem):
    list0 = em.itemtonav(mapitem, 'newnavitem')

    assert list0[0] == '[Item = newnavitem]'
    for entry in ['MapBinning', 'Regis', 'Type']:
        assert entry + ' = ' + str(mapitem[entry][0]) in list0

    for entry in ['StageXYZ', 'PtsX', 'PtsY']:
        assert entry + ' = ' + ' '.join(mapitem[entry]) in list0


def test_write_navfile(mapitem, navlines):
    pointitem = em.nav_item(navlines, '000')[0]

    outitems = [mapitem, pointitem]

    # adoc format
    file0 = 'testnav1.nav'

    for xml in [True, False]:
        em.write_navfile(file0, outitems, xml=xml)

        newlines = em.loadtext(file0)
        newnav = em.fullnav(newlines)

        assert mapitem in newnav
        assert pointitem in newnav


def test_newID(navlines):
    allitems = em.fullnav(navlines)

    assert em.newID(allitems, 0) == 0
    assert em.newID(allitems, 1403410986) == 1403410986
    assert em.newID(allitems, 1403410987) == 1403410988


def test_newreg(mapitem, navlines):
    pointitem = em.nav_item(navlines, '000')[0]

    testitems0 = [mapitem, pointitem]

    assert em.newreg(testitems0) == 2

    pointitem['Regis'][0] = 19

    assert em.newreg(testitems0) == 20


def test_fullnav(navlines, navlines_xml):
    for lines in (navlines, navlines_xml):

        allitems = em.fullnav(lines)

        assert type(allitems) is list
        assert len(allitems) == 6

        for item in allitems:
            assert type(item) is dict
            assert '# Item' in item.keys()
            assert 'PtsX' in item.keys()
            assert 'Type' in item.keys()

        assert item['GroupID'] == ['1074138545']


def test_xmltonav(navlines, navlines_xml, capsys):
    with pytest.raises(ValueError):
        em.xmltonav(navlines)
        captured = capsys.readouterr()
        assert 'XML format!' in captured.err

    allitems = em.fullnav(navlines)

    items0 = em.xmltonav(navlines_xml)

    assert items0 == allitems


def test_duplicate_items(navlines):
    for flag in [None, 'prefix', 'reg']:
        allitems = em.fullnav(navlines)
        if flag is None:
            dup0 = em.duplicate_items(allitems)
        elif flag == 'prefix':
            dup0 = em.duplicate_items(allitems, prefix=flag)
        elif flag == 'reg':
            dup0 = em.duplicate_items(allitems, reg=False)

        assert len(dup0) == 9

        for idx in [-3, -2, -1]:
            item = dict(dup0[idx])
            origitem = dict(allitems[idx])

            if not flag == 'reg':
                assert item['Regis'] == [str(em.newreg(allitems))]
                item.pop('Regis')
                origitem.pop('Regis')

            if flag == 'prefix':
                assert item['# Item'] == flag + origitem['# Item']
                item.pop('# Item')
                origitem.pop('# Item')

            assert item['MapID'] == [str(em.newID(allitems, int(origitem['MapID'][0])))]
            item.pop('MapID')
            origitem.pop('MapID')

            assert item == origitem

    # test map
    allitems = em.fullnav(navlines)

    dup1 = em.duplicate_items(allitems, maps=True)

    assert len(dup1) == 10

    for idx in [-4, -3, -2, -1]:

        item = dict(dup1[idx])

        if idx == -4:
            # original map
            origitem = dict(allitems[0])
        else:
            origitem = dict(allitems[idx])

        assert item['Regis'] == [str(em.newreg(allitems))]
        item.pop('Regis')
        origitem.pop('Regis')

        if idx == -4:
            assert item['MapID'] == [str(em.newID(allitems, int(origitem['MapID'][0])) + 1)]
        else:
            assert item['MapID'] == [str(em.newID(allitems, int(origitem['MapID'][0])))]

        item.pop('MapID')
        origitem.pop('MapID')

        if idx > -4:
            assert item['DrawnID'] == dup1[-4]['MapID']
            item.pop('DrawnID')
            origitem.pop('DrawnID')

        assert item == origitem


def test_map_matrix(mapitem):
    matrix = em.map_matrix(mapitem)
    assert (matrix == np.array(expected["map_matrix"])).all()


# TODO: mergemap + call_blendmont

def test_realign_map(mapitem, navlines, capsys):
    allitems = em.fullnav(navlines)
    ptitem = allitems[-1]

    realignmap1 = em.realign_map(ptitem, allitems)

    assert realignmap1 == mapitem

    assert em.realign_map(mapitem, allitems) == []

    captured = capsys.readouterr()
    assert 'No map found to realign' in captured.out
    assert mapitem['# Item'] in captured.out


def test_imcrop(capsys):
    testim = np.random.random([7, 7])

    with pytest.raises(TypeError):
        a = em.imcrop([1], 2, np.array([3]))
        captured = capsys.readouterr()
        assert 'list or numpy array' in captured.err

    im2 = em.imcrop(testim, [5, 3], [3, 3])
    assert (im2 == testim[0:5, :][:, 1:4]).all

    im3 = em.imcrop(testim, [2, 1], [3, 6])
    assert im3.shape == (2, 4)
    assert (im3 == testim[0:2, :][:, 0:4]).all

    im4 = em.imcrop(testim, [4, 6], [4, 1])
    assert im4.shape == (2, 1)
    assert (im4 == testim[:, 5][-2:]).all


def test_img2polygon(capsys):
    testim = imread('test_files/mask1.tif')
    testim1 = (testim / 245).astype(bool)

    for im in [testim, testim1]:
        poly = em.img2polygon(im, 4, [11, 7], 5)

        assert (poly == [[14., 7.],
                         [14., 8.],
                         [11., 8.],
                         [11., 8.],
                         [9., 9.],
                         [6., 9.],
                         [6., 7.],
                         [7., 5.],
                         [9., 3.],
                         [10., 2.],
                         [12., 3.],
                         [13., 5.],
                         [13., 7.]]).all

        poly = em.img2polygon(im, 7, [3, 3], 4)
        assert (poly == [[5., 3.],
                         [4., 3.],
                         [4., 6.],
                         [3., 3.],
                         [3., 3.],
                         [3., 3.],
                         [3., 3.],
                         [2., 1.],
                         [3., 1.],
                         [4., 2.],
                         [5., 2.]]).all

        poly = em.img2polygon(im, 7, [3, 3], 8)
        assert (poly == [[5., 3.],
                         [7., 9.],
                         [3., 3.],
                         [3., 3.],
                         [3., 3.],
                         [2., 1.],
                         [4., 1.],
                         [5., 2.]]).all

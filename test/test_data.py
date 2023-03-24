import os

example_mapz = os.path.join('test_files', 'maps.tgz')
example_map = os.path.abspath(os.path.join('test_files', 'MMM_01.mrc'))

if not os.path.exists(example_map):
    try:
        os.system('tar xvfz ' + example_mapz + ' -C ' + 'test_files')
    except OSError as e:
        pass
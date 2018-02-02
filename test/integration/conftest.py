def pytest_addoption(parser):
    parser.addoption('--fake', action='store_true', default=False,
                     help='don\'t run the code, reuse the result from '
                          'last tests')

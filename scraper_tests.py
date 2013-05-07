from glob import glob
import SimpleHTTPServer
import SocketServer
import threading
import unittest

from juriscraper.lib.importer import build_module_list

# TODO: Make sure logging is disabled.

PORT = 8080


class TestServer(SocketServer.TCPServer):
    allow_reuse_address = True


class ScraperExampleTest(unittest.TestCase):
    def setUp(self):
        # Due to requests not supporting the file scheme, we are forced to run 
        # our own server. See: https://github.com/kennethreitz/requests/issues/847
        Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
        httpd = TestServer(('', PORT), Handler)
        httpd_thread = threading.Thread(target=httpd.serve_forever)
        httpd_thread.setDaemon(True)
        httpd_thread.start()

    def tearDown(self):
        pass

    def test_scrape_all_example_files(self):
        '''Finds all the $module_example* files and tests them with the sample
        scraper.
        '''
        module_strings = build_module_list('opinions')
        for module_string in module_strings:
            package, module = module_string.rsplit('.', 1)
            mod = __import__("%s.%s" % (package, module),
                             globals(),
                             locals(),
                             [module])
            if 'backscraper' not in module_string:
                paths = glob('%s_example*' % module_string.replace('.', '/'))
                for path in paths:
                    full_url = 'http://localhost:%s/%s' % (PORT, path)
                    site = mod.Site()
                    site.url = full_url
                    # We always GET when we test locally.
                    site.method = 'GET'
                    site.parse()


if __name__ == '__main__':
    unittest.main()

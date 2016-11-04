from bs4 import BeautifulSoup as bs
import re
from threading import Thread
import requests
import os, sys
import urllib.parse
import unicodedata
from queue import Queue
import time



class Parser:
    def __init__(self):
        pass

    @staticmethod
    def parse_url_file(file_stream):
        soup_file = bs(file_stream, 'html.parser')
        all_script = soup_file.find_all('script')
        for s in all_script:
            if 'token' in s.string:
                prob_urls = re.search("(?P<url>https?://[^\s]+)", s.string).group('url').split('url')
                for p in prob_urls:
                    if 'token' in p and '1080' in p:
                        for t in p.split(','):
                            if 'token' in t and t.startswith('":'):
                                return t.split('":')[1]


class Content:
    def __init__(self):
        self.file_name_to_save = None
        self.url_content = None


    @staticmethod
    def _sanitize(name):
        str_tmp = urllib.parse.unquote(name)
        str_tmp = unicodedata.normalize('NFKD', str_tmp).encode('ASCII', 'ignore')
        str_tmp = str_tmp.decode('utf8').replace(' ', '_').replace(':', '-')
        return str_tmp



    def download_url_content(self, url, file_name, repo_dir):
        print("Initializing download url: {}".format(url))
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
        }

        if url.startswith('"') and url.endswith('"'):
            url = url.split('"')[1]

        try:
            r = requests.get(url, stream=True, headers=headers)
        except Exception as ex:
            raise ex

        self.save(file_name=file_name, r=r, repo_dir=repo_dir)

    def save(self, file_name, r, repo_dir):
        file_name = "{}.mp4".format(Content._sanitize(file_name))

        print("Salvando o arquivo: {} no diretorio {}".format(file_name, repo_dir))

        file_to_save = '{}/{}'.format(repo_dir, file_name)
        try:
            with open(file_to_save, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        except Exception as ex:
            raise ex

        print("File {}: [DONE]".format(file_name))
        return


class HtmlRead:
    def __init__(self):
        self.file_name = "page.dad"
        self.c = Content()
        self.q = Queue()

    @staticmethod
    def _clean_file(f):
        f.seek(0)
        f.truncate()

    @staticmethod
    def _check_stat_file(out_q, file_):
        print("Reading input file....")
        mtime_pre = os.stat(file_).st_mtime

        while True:
            mtime_cur = os.stat(file_).st_mtime
            if mtime_cur > mtime_pre:
                out_q.put(True)
                mtime_pre = mtime_cur

            time.sleep(1)

    def _get_file_content(self, in_q, repo_dir):
        while True:
            item_q = in_q.get()
            if item_q:
                with open(self.file_name, 'r+') as fp:
                    data = fp.readlines()
                    fp.seek(0)
                    if data and isinstance(data, list):
                        if 1 < len(data[0]) < 1024:
                            print("\n\nFile name: {}".format(data[0]))
                            file_name = data[0].split("\n")[0]
                            self._clean_file(fp)
                            fp.close()
                            continue
                        else:
                            content = data[0] if data[0] != '\n' else data[1]
                            print('Initializing url parser...')
                            url = Parser.parse_url_file(content)
                            if url:
                                fp.truncate()
                                print("url found: {}".format(url))
                                t = Thread(target=self.c.download_url_content, args=(url, file_name, repo_dir))
                                t.start()
                            else:
                                print("Url not found in input file!")
                                # self._clean_file(fp)
            in_q.task_done()

    def wait_from_file(self, repo_dir):
        thr_get_f = Thread(target=self._get_file_content, args=(self.q, repo_dir,))
        thr_chk_f = Thread(target=HtmlRead._check_stat_file, args=(self.q, self.file_name,))

        thr_get_f.start()
        thr_chk_f.start()


    @staticmethod
    def wait_from_std(repo_dir):

        print("Reading standard input (keyboard)....")

        while True:
            inp = input("input data \n")

            if 1 < len(inp) < 1024:
                print("\n\nFile name: {}".format(inp))
                file_name = inp
            else:
                print(inp)
                sys.exit(1)
                url = Parser.parse_url_file(str(inp))
                if url:
                    c = Content()

                    print("url found: {}".format(url))
                    t = Thread(target=c.download_url_content, args=(url, file_name, repo_dir))
                    t.start()

    def run(self, repo_dir):
        file_name = None
        os.system('clear')

        try:
            self.wait_from_file(repo_dir=repo_dir)
            #self.wait_from_std(repo_dir=repo_dir)
        except Exception as ex:
            raise ex



def main(argv):
    input_file_name = 'page.dad'

    if len(argv) != 3 or argv[1] != '-d':
        print("ERROR Usage: python3 html_read.py -d 'repo_dir'")
        sys.exit(1)

    try:
        os.stat(input_file_name)
    except FileNotFoundError:
        print("Need to create an empty file named {}".format(input_file_name))
        sys.exit(1)

    dist_dir = argv[2]

    h = HtmlRead()
    h.run(dist_dir)


if __name__ == "__main__":
    main(sys.argv)

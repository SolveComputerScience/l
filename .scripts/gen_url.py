# l by SolveComputerScience
#
# To the extent possible under law, the person who associated CC0 with
# SolveComputerScience has waived all copyright and related or neighboring rights
# to l.
#
# You should have received a copy of the CC0 legalcode along with this
# work.  If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.
import hashlib
import pathlib
import sys
import qrcode
from urllib.parse import urlparse, urljoin
import argparse
import slugify
import logging
import re


URL_SUFFIX: str = 'https://SolveComputerScience.github.io/l'
DST_DIR: str = '../.'
PAGE_TIMEOUT: int = 2
UMAMI_BASE_CODE: str = 'src="https://umami.franco.net.eu.org/script.js" data-website-id="763262f8-2ecc-4cec-adae-9318f97128c9"'
DEFAULT_DATA_TAG: str = 'SolveComputerScience'


logging.basicConfig(level=logging.INFO)


def gen_umami_code(data_tag: str) -> str:
    return f'''<script defer {UMAMI_BASE_CODE} data-tag="{data_tag}"></script>'''


def check_input(url: str) -> bool:
    is_url: bool = False

    parsed_url = urlparse(url)
    if parsed_url.scheme == 'https' and bool(parsed_url.netloc):
        is_url = True

    return is_url


def url_type(url: str) -> str:
    if not check_input(url):
        raise argparse.ArgumentTypeError(f'invalid URL: "{url}", please provide a valid URL starting with https://')
    return url


def get_file_name(hash_hex: str, file_type: str, existing_file: str = '') -> str:
    file: str
    if existing_file:
        # Replace file suffix.
        file = str(pathlib.Path(existing_file).with_suffix(f'.{file_type}'))
    else:
        file = f'{hash_hex}.{file_type}'

    return file


def create_redirect_file(original_url: str, page_title: str = '', existing_file: str = '', overwrite: bool = False) -> str:
    hash_hex: str
    if existing_file:
        # We need to get the exising filename to be used as hash.
        hash_hex = pathlib.Path(existing_file).stem
    else:
        hash_hex = hashlib.blake2b(original_url.encode(), digest_size=12).hexdigest()

    file: str = get_file_name(hash_hex, 'html', existing_file)
    
    html_content: str = f"""<!DOCTYPE html><html><head><title>{page_title}</title><link rel="stylesheet" href=".core.css">{gen_umami_code(slugify.slugify(page_title))}<meta http-equiv="refresh" content="{PAGE_TIMEOUT}; url={original_url}" /></head><body><p>This redirection page is managed by <a href="https://www.youtube.com/@SolveComputerScience">SolveComputerScience</a></p><p>If you are not redirected in {PAGE_TIMEOUT} seconds, <a href="{original_url}">click here</a>.</p></body></html>"""
 
    dst_file: pathlib.Path = pathlib.Path(DST_DIR, file)
    if (dst_file.is_file() and overwrite) or (not dst_file.is_file()):
        pathlib.Path(DST_DIR, file).write_text(html_content)
    elif dst_file.is_file():
        raise ValueError(f'cannot overwrite {file}, please pass the overwrite option')

    return hash_hex, file


def create_qr(hash_hex: str, existing_file: str = '') -> tuple[str, str]:
    file: str = get_file_name(hash_hex, 'png', existing_file)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    data: str = ''.join([URL_SUFFIX, '/', hash_hex, '.html'])
    logging.info(data)

    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(str(pathlib.Path(DST_DIR, file)))

    return hash_hex, file


def search(
   search_string: str,
   regex: bool = False,
   verbose: bool = False,
   print_url: bool = False) -> str:
    directory: pathlib.Path = pathlib.Path(DST_DIR)

    if not regex:
        search_string = re.escape(search_string)

    for path in directory.rglob('*.html'):
        if path.is_file():
            file: str = path.read_text()
            if re.search(search_string, file):
                relative_file: str = path.stem
                logging.info(f'{relative_file}')

                if print_url:
                    url: str = urljoin(URL_SUFFIX, str(path))
                    logging.info(f'{url}')

                if verbose:
                    print(file, end='\n\n')


def main():
    parser = argparse.ArgumentParser(description='Manage redirects.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Create.
    create_parser = subparsers.add_parser('create', help='Create a new redirect file')
    create_parser.add_argument('url', type=url_type, help='The URL to create')
    create_parser.add_argument('title', type=str, help='The title for the URL')
    create_parser.add_argument('--overwrite', action='store_true', help='Overwrite an existing file')

    # Update.
    update_parser = subparsers.add_parser('update', help='Update an existing redirect file')
    update_parser.add_argument('url', type=url_type, help='The URL to update')
    update_parser.add_argument('file', type=str, help='The file associated with the update')
    update_parser.add_argument('--title', type=str, help='The new title for the URL', default=DEFAULT_DATA_TAG)

    # Search.
    update_parser = subparsers.add_parser('search', help='Update an existing redirect file')
    update_parser.add_argument('search_string', type=str, help='A string or regex pattern to search for')
    update_parser.add_argument('--regex', action='store_true', help='Treat the input string as regex')
    update_parser.add_argument('--verbose', action='store_true', help='Print the whole file on match')
    update_parser.add_argument('--print-url', action='store_true', help='Print the final URL on match')

    args = parser.parse_args()

    if args.command == 'create':
        logging.info(f'Creating entry: URL={args.url}, TITLE={args.title}')
        hash_hex, html_file = create_redirect_file(
            args.url,
            args.title,
            overwrite=True if args.overwrite else False
        )
        _, qr_file = create_qr(hash_hex)
    elif args.command == 'update':
        logging.info(f'Updating entry: URL={args.url}, TITLE={args.title}, FILE={args.file}')
        existing_file: str = args.file
        hash_hex, html_file = create_redirect_file(args.url, args.title, existing_file)
        _, qr_file = create_qr(hash_hex, existing_file)
    elif args.command == 'search':
        logging.info(f'searching for "{args.search_string}"...')
        search(
            args.search_string,
            regex=True if args.regex else False,
            verbose=True if args.verbose else False,
            print_url=True if args.print_url else False
        )


if __name__ == '__main__':
    main()

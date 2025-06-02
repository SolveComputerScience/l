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
from urllib.parse import urlparse
import argparse
import slugify


URL_SUFFIX: str = 'https://SolveComputerScience.github.io/l'
DST_DIR: str = '../.'
PAGE_TIMEOUT: int = 2
UMAMI_BASE_CODE: str = 'src="https://umami.franco.net.eu.org/script.js" data-website-id="763262f8-2ecc-4cec-adae-9318f97128c9"'
DEFAULT_DATA_TAG: str = 'SolveComputerScience'


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


def create_redirect_file(original_url: str, page_title: str = '', existing_file: str = '') -> str:
    hash_hex: str
    if existing_file:
        # We need to get the exising filename to be used as hash.
        hash_hex = pathlib.Path(existing_file).stem
    else:
        hash_hex = hashlib.blake2b(original_url.encode(), digest_size=12).hexdigest()

    file: str = get_file_name(hash_hex, 'html', existing_file)
    
    html_content: str = f"""<!DOCTYPE html><html><head><title>{page_title}</title>{gen_umami_code(slugify.slugify(page_title))}<meta http-equiv="refresh" content="{PAGE_TIMEOUT}; url={original_url}" /></head><body><p>This redirection page is managed by <a href="https://www.youtube.com/@SolveComputerScience">SolveComputerScience</a></p><p>If you are not redirected in {PAGE_TIMEOUT} seconds, <a href="{original_url}">click here</a>.</p></body></html>"""
    
    pathlib.Path(DST_DIR, file).write_text(html_content)

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
    print(data)

    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(str(pathlib.Path(DST_DIR, file)))

    return hash_hex, file


def main():
    parser = argparse.ArgumentParser(description='Manage redirects.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # Create command.
    create_parser = subparsers.add_parser('create', help='Create a new redirect file')
    create_parser.add_argument('url', type=url_type, help='The URL to create')
    create_parser.add_argument('title', type=str, help='The title for the URL')

    # Update command.
    update_parser = subparsers.add_parser('update', help='Update an existing redirect file')
    update_parser.add_argument('url', type=url_type, help='The URL to update')
    update_parser.add_argument('file', type=str, help='The file associated with the update')
    update_parser.add_argument('--title', type=str, help='The new title for the URL', default=DEFAULT_DATA_TAG)

    args = parser.parse_args()

    if args.command == 'create':
        print(f'Creating entry: URL={args.url}, TITLE={args.title}')
        hash_hex, html_file = create_redirect_file(args.url, args.title)
        _, qr_file = create_qr(hash_hex)
    elif args.command == 'update':
        print(f'Updating entry: URL={args.url}, TITLE={args.title}, FILE={args.file}')
        existing_file: str = args.file
        hash_hex, html_file = create_redirect_file(args.url, args.title, existing_file)
        _, qr_file = create_qr(hash_hex, existing_file)


if __name__ == '__main__':
    main()

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


URL_SUFFIX='https://SolveComputerScience.github.io/l'
DST_DIR='../.'


def check_input(url: str) -> bool:
    is_url: bool = False

    parsed_url = urlparse(url)
    if parsed_url.scheme == 'https' and bool(parsed_url.netloc):
        is_url = True

    return is_url

def get_file_name(hash_hex: str, file_type: str, existing_file: str = '') -> str:
    file: str
    if existing_file:
        # Replace file suffix.
        file = str(pathlib.Path(existing_file).with_suffix(f'.{file_type}'))
    else:
        file = f'{hash_hex}.{file_type}'

    return file


def create_redirect_file(original_url: str, existing_file: str = '') -> str:
    hash_hex: str
    if existing_file:
        # We need to get the exising filename to be used as hash.
        hash_hex = pathlib.Path(existing_file).stem
    else:
        hash_hex = hashlib.blake2b(original_url.encode(), digest_size=12).hexdigest()

    file: str = get_file_name(hash_hex, 'html', existing_file)
    
    html_content: str = f"""<!DOCTYPE html><html><head><meta http-equiv="refresh" content="0; url={original_url}" /></head><body><p>This redirection page is managed by <a href="https://www.youtube.com/@SolveComputerScience">SolveComputerScience</a></p><p>If you are not redirected, <a href="{original_url}">click here</a>.</p></body></html>"""
    
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


if __name__ == '__main__':
    ok: bool = False
    usage: bool = False

    if len(sys.argv) == 3:
        # Update.
        url_new: str = sys.argv[1]
        if check_input(url_new):
            existing_file: str = sys.argv[2]
            hash_hex, html_file = create_redirect_file(url_new, existing_file)
            _, qr_file = create_qr(hash_hex, existing_file)
            ok = True

    elif len(sys.argv) == 2:
        # Create.
        url: str = sys.argv[1]
        if check_input(url):
            hash_hex, html_file = create_redirect_file(url)
            _, qr_file = create_qr(hash_hex)
            ok = True

    else:
        usage = True
        print('python -m gen_short_link URL')
        print('python -m gen_short_link URL EXISTING_FILE')

    if not usage:
        if ok:
            print(f'{html_file}, {qr_file}')
        else:
            print('input is not a valid URL')


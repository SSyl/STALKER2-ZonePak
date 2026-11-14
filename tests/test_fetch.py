import hashlib
import http.client
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

from zonepak import fetch
from zonepak.project import Config


def tool_zip(exe: bytes) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        z.writestr('LICENSE-MIT', 'license')
        z.writestr('repak.exe', exe)
    return out.getvalue()


class EnsureTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.third_party = Path(self.tmp.name) / 'third_party'
        self.data = tool_zip(b'repak binary')
        download = fetch.Download('repak.exe', 'https://example.invalid/release', 'https://example.invalid/repak.zip',
                                  hashlib.sha256(self.data).hexdigest())
        for patch in (mock.patch.object(fetch, 'THIRD_PARTY', self.third_party),
                      mock.patch.dict(fetch.DOWNLOADS, {'repak': download})):
            patch.start()
            self.addCleanup(patch.stop)
        self.opened = []

    def tearDown(self):
        self.tmp.cleanup()

    def ensure(self, answers, data=None):
        replies = iter(answers)
        return fetch.ensure('repak', ask=lambda question: next(replies), open_page=self.opened.append,
                            interactive=True, fetch=lambda url: self.data if data is None else data)

    def test_existing_tool_is_used_without_asking(self):
        self.third_party.mkdir()
        (self.third_party / 'repak.exe').write_bytes(b'already here')
        self.assertEqual(self.ensure([]), self.third_party / 'repak.exe')

    def test_yes_downloads_and_extracts_only_the_exe(self):
        path = self.ensure(['y'])
        self.assertEqual(path.read_bytes(), b'repak binary')
        self.assertEqual(sorted(p.name for p in self.third_party.iterdir()), ['repak.exe'])

    def test_other_answers_ask_again(self):
        answers = ['', 'maybe', 'Y']
        asked = []
        fetch.ensure('repak', ask=lambda question: asked.append(question) or answers[len(asked) - 1],
                     interactive=True, fetch=lambda url: self.data)
        self.assertEqual(len(asked), 3)
        self.assertTrue((self.third_party / 'repak.exe').is_file())

    def test_no_opens_the_release_page_and_explains(self):
        with self.assertRaisesRegex(fetch.FetchError, r'extract repak\.exe from it into .*third_party'):
            self.ensure(['n'])
        self.assertEqual(self.opened, ['https://example.invalid/release'])
        self.assertFalse(self.third_party.exists())

    def test_hash_mismatch_writes_nothing(self):
        with self.assertRaisesRegex(fetch.FetchError, 'Nothing was written'):
            self.ensure(['y'], data=tool_zip(b'tampered'))
        self.assertFalse(self.third_party.exists())

    def test_without_a_terminal_it_explains_instead_of_asking(self):
        with self.assertRaisesRegex(fetch.FetchError, 'repak is not set'):
            fetch.ensure('repak', ask=lambda question: self.fail('asked'), interactive=False)

    def test_stdin_that_is_not_a_terminal_counts_as_no_terminal(self):
        with mock.patch.object(fetch.sys, 'stdin', mock.Mock(isatty=lambda: False)), \
                self.assertRaisesRegex(fetch.FetchError, 'repak is not set'):
            fetch.ensure('repak', ask=lambda question: self.fail('asked'))

    def test_end_of_input_explains_instead_of_crashing(self):
        def ask(question):
            raise EOFError
        with self.assertRaisesRegex(fetch.FetchError, r'repak is not set .* extract repak\.exe'):
            fetch.ensure('repak', ask=ask, open_page=self.opened.append, interactive=True)

    def test_dropped_connection_is_a_fetch_error(self):
        with mock.patch('urllib.request.urlopen', side_effect=http.client.IncompleteRead(b'')), \
                self.assertRaisesRegex(fetch.FetchError, 'cannot download'):
            fetch._get('https://example.invalid/repak.zip')


class RequireTest(unittest.TestCase):
    def test_configured_tool_skips_fetch(self):
        with mock.patch.object(fetch, 'ensure', side_effect=AssertionError('fetched')):
            self.assertEqual(Config(repak=Path('C:/Tools/repak.exe')).require('repak'), Path('C:/Tools/repak.exe'))

    def test_missing_tool_goes_through_fetch(self):
        with mock.patch.object(fetch, 'ensure', return_value=Path('third_party/repak.exe')) as ensure:
            self.assertEqual(Config().require('repak'), Path('third_party/repak.exe'))
            Config(cli=True).require('repak')
        self.assertEqual(ensure.call_args_list, [mock.call('repak', cli=False), mock.call('repak', cli=True)])

    def test_manual_steps_suggest_the_flag_only_on_the_command_line(self):
        self.assertNotIn('--repak', fetch.manual_steps('repak'))
        self.assertIn('or pass --repak.', fetch.manual_steps('repak', cli=True))

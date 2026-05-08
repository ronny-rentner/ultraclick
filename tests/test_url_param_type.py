import unittest

from click.testing import CliRunner

import ultraclick as click


@click.command()
@click.argument("url", type=click.URL)
def url_cli(url):
    return url


class TestURLParamType(unittest.TestCase):
    def test_accepts_absolute_http_url(self):
        result = CliRunner().invoke(url_cli, ["http://example.com/path"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("http://example.com/path", result.output)

    def test_accepts_absolute_https_url(self):
        result = CliRunner().invoke(url_cli, ["https://example.com/path"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("https://example.com/path", result.output)

    def test_rejects_relative_value(self):
        result = CliRunner().invoke(url_cli, ["example.com/path"])

        self.assertEqual(result.exit_code, 2)
        self.assertIn("not an absolute HTTP(S) URL", result.output)

    def test_rejects_non_http_scheme(self):
        result = CliRunner().invoke(url_cli, ["ftp://example.com/path"])

        self.assertEqual(result.exit_code, 2)
        self.assertIn("not an absolute HTTP(S) URL", result.output)


if __name__ == "__main__":
    unittest.main()

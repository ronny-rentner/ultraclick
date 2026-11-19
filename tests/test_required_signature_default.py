import unittest

import ultraclick as click


class TestRequiredSignatureDefault(unittest.TestCase):
    def test_required_command_option_with_signature_default_is_rejected(self):
        with self.assertRaisesRegex(TypeError, r"App\.label\(\): 'icon_dir' has the signature default None"):
            class App:
                @click.command()
                @click.option('--icon-dir', required=True)
                def label(self, title, icon_dir=None):
                    pass

    def test_required_init_option_with_signature_default_is_rejected(self):
        with self.assertRaisesRegex(TypeError, r"App\.__init__\(\): 'env' has the signature default 'development'"):
            class App:
                @click.option('--env', required=True)
                def __init__(self, env='development'):
                    pass

    def test_required_argument_with_signature_default_is_rejected(self):
        with self.assertRaisesRegex(TypeError, r"greet\(\): 'name' has the signature default 'world'"):
            @click.argument('NAME', required=True)
            def greet(name='world'):
                pass

    def test_required_option_without_signature_default_is_accepted(self):
        @click.command()
        @click.option('--icon-dir', required=True)
        def label(icon_dir):
            return icon_dir

        label = click.apply_decorators(label)

        self.assertTrue(label.params[0].required)


if __name__ == '__main__':
    unittest.main()

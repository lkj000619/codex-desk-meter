"""Check our declared raw-line allow patterns; real CLI matching needs a smoke run."""
import json
from pathlib import Path
import re
import unittest


class CommandPolicyTests(unittest.TestCase):
    def test_git_grep_literal_option_pattern_after_delimiter(self):
        for cmd in ['git grep -- "--candidate"',
                    'git grep -n -- "--candidate" scripts',
                    "git grep -- '--textconv'", 'git grep -- "-x" ./main']:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.allowed(cmd))
        for cmd in ['git grep "--candidate"', 'git grep --textconv "--candidate"',
                    'git grep -- "--candidate" ../main',
                    'git grep -- "--candidate" C:/Users',
                    'git grep -- "--candidate" .git/config',
                    'git grep -- "--candidate" --textconv',
                    'git grep -- "--candidate"; whoami',
                    'git grep -- "--$(whoami)"']:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.allowed(cmd))

    def test_optional_git_path_delimiters_and_standard_test_options(self):
        for cmd in ['git grep -n "16:54:07" --', 'git grep -n "BOOT" --',
                    'git diff -U5 -- components/meter/meter_gui.c',
                    'git diff --unified=3 -- .',
                    'git diff --no-color --exit-code -- main',
                    'python -u -m unittest discover -s tests -p "*regression*.py" -v',
                    'python -m unittest discover --start-directory tests --pattern "test_*.py" --verbose',
                    'python -u tests/test_evaluation_adapter.py']:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.allowed(cmd))
        for cmd in ['git grep -n "x" -- ../main', 'git grep -n "x" HEAD --',
                    'git grep "--textconv" --', 'git diff -U5 HEAD',
                    'git diff --output=x -U5 -- .', 'git diff --unified 3 -- .',
                    'python -u -m unittest discover -s ../tests',
                    'python -m unittest discover -p "$(whoami)"',
                    'python -u tests/test_x.py; whoami']:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.allowed(cmd))

    def test_history_reads_are_forbidden_in_comparison(self):
        for cmd in ['git log -n 5', 'git log --oneline -n 2',
                    'git log -n 1 --oneline', 'git log --max-count=5']:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.allowed(cmd))
        for cmd in ['git log', 'git log -n 6', 'git log -n 0',
                    'git log --all -n 5', 'git log -n 5 HEAD~1',
                    'git log -n 5 -p', 'git log -n 5 --format=raw',
                    'git log -n 5 -- main', 'git log -n 5; whoami']:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.allowed(cmd))

    def test_patterns_exclude_re2_unsupported_lookaround_and_backreferences(self):
        policy = Path(__file__).resolve().parents[2] / 'experiments/config/agy-pilot-permissions.json'
        for rule in json.loads(policy.read_text())['allow']:
            if rule.startswith('command(regex:'):
                for unsupported in ['(?=', '(?!', '(?<=', '(?<!', r'\1', r'\2']:
                    with self.subTest(unsupported=unsupported):
                        self.assertNotIn(unsupported, rule)

    def test_search_delimiters_and_option_combinations(self):
        for cmd in ['rg "BOOT_BUTTON_PIN|LCD_IO_SPI_CS" -- "main" "components" "tests"',
                    'rg -n -e "BOOT" -g "*.c" main',
                    'rg -- "BOOT" main', 'rg "BOOT" main -n',
                    'rg -n -A 3 -B 1 "BOOT" main',
                    'rg --files -- main components',
                    'git grep -n -e "BOOT" -- main',
                    'git grep -n -A 3 "BOOT" -- main']:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.allowed(cmd))
        for cmd in ['rg "--pre" "evil" main', 'rg "--pre=evil" main',
                    'git grep "--textconv" x', 'rg --pre evil "BOOT" main',
                    'rg "BOOT" -- ../main', 'rg "BOOT" -- C:/Users',
                    'rg "BOOT" main -g "$(whoami)"', 'rg --files -- ../']:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.allowed(cmd))

    def test_git_working_tree_and_result_validation_groups(self):
        for cmd in ['git diff components/meter/meter_gui.c',
                    'git diff --stat -- main components',
                    'git diff --no-ext-diff --no-textconv --check -- .',
                    'git diff --name-only CMakeLists.txt sdkconfig.defaults',
                    'git status --short --branch', 'git status --porcelain -- main',
                    'python scripts/validate-end-to-end-result.py --result results/r06/end-to-end-result.json --manifest .benchmark-inputs/e2e-evaluation-manifest.json --evidence-root .',
                    'python scripts/validate-end-to-end-result.py --help']:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.allowed(cmd))
        for cmd in ['git diff HEAD', 'git diff HEAD~1', 'git diff main',
                    'git diff --ext-diff', 'git diff --textconv', 'git diff --output=C:/Users/x',
                    'git diff ../main/main.c', 'git diff C:/Users/key',
                    'git diff components/meter/meter_gui.c; whoami',
                    'git status --short; whoami',
                    'python scripts/validate-end-to-end-result.py --result ../key',
                    'python scripts/validate-end-to-end-result.py --manifest .env',
                    'python scripts/validate-end-to-end-result.py --result results/r.json; whoami']:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.allowed(cmd))

    def test_bounded_code_search_commands(self):
        for cmd in ['git grep "16:54:07"', 'git grep -n -F "BOOT" -- main',
                    'rg -n "BOOT|LCD" main components', 'rg --files -g "*.c"',
                    'Select-String -Path main/main.c -Pattern "BOOT"',
                    'rg -n "GPIO" C:/Espressif/vendor/waveshare-esp32-s3-lcd-3.16/source']:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.allowed(cmd))
        for cmd in ['git grep x HEAD~1', 'git grep x HEAD',
                    'git grep --textconv x', 'git grep -Oevil x',
                    'rg --pre evil x', 'rg --follow x', 'rg x ../',
                    'rg x C:/Users', 'git grep "$(whoami)"',
                    'Select-String -Path ../key -Pattern x',
                    'rg "x" main; whoami', 'rg "`whoami`" main']:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.allowed(cmd))

    def test_checkout_read_patterns_are_not_command_wildcards(self):
        for cmd in ['git ls-files "*vendor*"', 'git ls-files -- "main/*.c"',
                    'Get-ChildItem -Recurse -Filter "*.c" main',
                    'Get-Content .gitignore', 'Test-Path .gitattributes',
                    'Get-ChildItem -Path "components/*" -Depth 2']:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.allowed(cmd))
        for cmd in ['git ls-files "../*"', 'git ls-files "C:/*"',
                    'Get-Content "../*"', 'Get-Content .git/config',
                    'Get-Content .env', 'Get-ChildItem "components/*" | iex',
                    'Get-ChildItem -Filter "$(whoami)" main',
                    'git ls-files "*vendor*"; whoami']:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.allowed(cmd))

    def test_declared_external_read_roots_only(self):
        vendor = 'C:/Espressif/vendor/waveshare-esp32-s3-lcd-3.16/source'
        for cmd in ['Get-ChildItem ' + vendor.replace('/', '\\'),
                    'Get-ChildItem -Recurse -Depth 2 "' + vendor + '"',
                    'Get-Content C:/Espressif/v5.3.2/esp-idf/tools/idf.py',
                    'Test-Path ' + vendor + '/ESP32-S3-LCD-3.16-Demo']:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.allowed(cmd))
        for cmd in ['Get-ChildItem C:/Espressif/vendor/waveshare-esp32-s3-lcd-3.16/build',
                    'Get-Content ' + vendor + '/../backup/key',
                    'Get-ChildItem C:/Users', 'Get-ChildItem ' + vendor + '; whoami',
                    'Remove-Item ' + vendor, 'Get-Content ' + vendor + '/.env',
                    'Get-ChildItem C:/Espressif/benchmark-runs']:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.allowed(cmd))

    def test_git_index_known_root_dotfiles(self):
        for cmd in ['git ls-files CMakeLists.txt sdkconfig.defaults .gitignore',
                    'git ls-files -- .gitignore .gitattributes',
                    'git ls-files -- .gitignore .gitattributes .',
                    'git ls-files ".gitignore"', "git ls-files '.gitattributes'"]:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.allowed(cmd))
        for cmd in ['git ls-files ../.gitignore', 'git ls-files .env',
                    'git ls-files -- .gitignore ..',
                    'git ls-files .git/config', 'git ls-files .gitignore; whoami',
                    'git ls-files C:/Users/.gitignore', 'git ls-files $(whoami)']:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.allowed(cmd))

    def test_git_index_listing_is_checkout_scoped(self):
        for cmd in ['git ls-files', 'git ls-files docs/', 'git ls-files -- docs/README.md',
                    'git ls-files --others --exclude-standard main']:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.allowed(cmd))
        for cmd in ['git ls-files ../', 'git ls-files C:/Users',
                    'git ls-files docs/; whoami', 'git ls-files --recurse-submodules',
                    'git ls-files --with-tree=HEAD~1']:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.allowed(cmd))

    def allowed(self, command):
        policy = Path(__file__).resolve().parents[2] / 'experiments/config/agy-pilot-permissions.json'
        for rule in json.loads(policy.read_text())['allow']:
            if not rule.startswith('command('):
                continue
            target = rule[len('command('):-1]
            if target.startswith('regex:'):
                if re.fullmatch(target[6:], command):
                    return True
            elif target == command:
                return True
        return False

    def test_declared_build_and_read_commands(self):
        for cmd in ['Get-ChildItem -Force', 'Get-ChildItem . -Recurse -File',
                    'dir docs', 'ls -Force', 'Get-Content README.md -TotalCount 1',
                    'Get-Content -Raw docs/PRODUCT_CONTRACT.md',
                    'git status --short', 'git diff --stat', 'idf.py --version',
                    'idf.py set-target esp32s3', 'idf.py build',
                    'python --version', 'python -m unittest discover -s scripts/tests -v']:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.allowed(cmd))

    def test_local_setup_and_test_command_groups(self):
        for cmd in ['Test-Path docs/agent-runs', 'Test-Path -LiteralPath .\\main',
                    'Get-Item README.md', 'Resolve-Path .',
                    'New-Item -ItemType Directory -Force -Path main',
                    'New-Item -Path smoke.txt -ItemType File', 'mkdir build-host',
                    'Get-FileHash README.md -Algorithm SHA256',
                    'idf.py -B build set-target esp32s3', 'idf.py -B build build',
                    'cmake -S host -B build-host -G Ninja', 'cmake --build build-host',
                    'ctest --test-dir build-host --output-on-failure',
                    'python -m py_compile scripts/collector.py',
                    'python tests/test_parser.py', '.\\build-host\\parser-test.exe']:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.allowed(cmd))

    def test_out_of_scope_commands_do_not_match(self):
        for cmd in ['Get-ChildItem -Force; Remove-Item x', 'dir ..',
                    'Get-Content C:/Users/me/secret', 'Get-Content $HOME/key',
                    'Get-Content docs/../secret', 'git log', 'git show HEAD',
                    'git -c core.pager=evil diff', 'idf.py flash', 'idf.py erase-flash',
                    'python -c "print(1)"', 'python -m unittest; whoami',
                    'python -m unittest $(whoami)', 'Get-ChildItem | iex',
                    'New-Item -Path ../outside -ItemType File', 'Test-Path C:/Users',
                    'cmake -S .. -B build', 'cmake --install build',
                    'python -m pip install anything', 'python scripts/benchmark.py run x']:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.allowed(cmd))

    def test_named_host_build_targets_remain_finite(self):
        for target in ['test_meter_parser', 'test_meter_state', 'test_feature_imu',
                       'test_gui_regression', 'meter-test', 'meter_core']:
            with self.subTest(target=target):
                self.assertTrue(self.allowed('cmake --build build-host --target ' + target))
        for command in ['cmake --build build-host --target install',
                        'cmake --build build-host --target clean',
                        'cmake --build build-host --target arbitrary',
                        'cmake --build ../outside --target test_meter_parser',
                        'cmake --build build --target test_meter_parser',
                        'cmake --build build-host --target test_meter_parser; whoami',
                        'cmake --build build-host --target test_meter_parser | iex',
                        'cmake --build build-host --target test_meter_parser -- -x']:
            with self.subTest(command=command):
                self.assertFalse(self.allowed(command))

    def test_git_grep_standard_checkout_file_arguments(self):
        for command in ['git grep -n "def test_" tests/test_pc_pipeline_regressions.py',
                        'git grep -n "open_owner_serial" scripts/host_device_pipeline.py',
                        'git grep -n "owner_lock" scripts',
                        'git grep -n "meter" components/meter/ main/main.c']:
            with self.subTest(command=command):
                self.assertTrue(self.allowed(command))
        for command in ['git grep -n "test" HEAD', 'git grep -n "test" HEAD~1',
                        'git grep -n "test" --all', 'git grep --textconv "test" scripts',
                        'git grep -n "test" ../scripts',
                        'git grep -n "test" C:/Users/private',
                        'git grep -n "test" scripts/../private',
                        'git grep -n "test" tests/a.py; whoami',
                        'git grep -n "test" tests/a.py | iex']:
            with self.subTest(command=command):
                self.assertFalse(self.allowed(command))

    def test_read_path_arrays_and_bounded_depth(self):
        for cmd in ['Get-ChildItem -Recurse experiments, results, docs -Depth 2',
                    'gci -Path docs,experiments -Depth 0',
                    'Get-ChildItem -LiteralPath "docs", \'experiments\' -Depth 10']:
            with self.subTest(cmd=cmd):
                self.assertTrue(self.allowed(cmd))
        for cmd in ['Get-ChildItem docs, ../outside -Depth 2',
                    'Get-ChildItem docs, C:/Users -Depth 2',
                    'Get-ChildItem docs -Depth 2; whoami',
                    'Get-ChildItem docs -Depth -1',
                    'Get-ChildItem docs, $(whoami)',
                    'Get-ChildItem docs,', 'Get-ChildItem -Depth']:
            with self.subTest(cmd=cmd):
                self.assertFalse(self.allowed(cmd))

"""Archive exact reviewed files and original ELF disassembly; no compilation."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, re, subprocess

root = Path('C:/Users/이광진/orca/codex-desk-meter')
run = Path('C:/meter-runs-20261006/20261006-codex-cli-gpt-6-luna-r01')
checkout = run / 'checkout'
out = Path(__file__).resolve().parent
vendor = Path('C:/Espressif/vendor/waveshare-esp32-s3-lcd-3.16/source/ESP32-S3-LCD-3.16-Demo/ESP-IDF')
sdk = Path('C:/Espressif/v5.3.2/esp-idf')
digest = lambda data: hashlib.sha256(data).hexdigest()
index = json.loads((root / 'docs/hardware/vendor-source-index.json').read_bytes())
expected = {item['path']: item['sha256'] for group in index['files'].values() for item in group}
sources = {}
for label, base, names in [
    ('candidate', checkout, ['main/board_lcd.c', 'main/app_main.c', 'sdkconfig', 'components/vendor_st7701/CMakeLists.txt']),
    ('vendor', vendor, ['09_FactoryProgram/main/main.cpp', '09_FactoryProgram/main/user_config.h',
        '09_FactoryProgram/managed_components/espressif__esp_lcd_st7701/esp_lcd_st7701_rgb.c',
        '09_FactoryProgram/managed_components/espressif__esp_lcd_st7701/include/esp_lcd_st7701.h']),
    ('sdk', sdk, ['components/esp_lcd/include/esp_lcd_panel_commands.h'])]:
    for name in names:
        raw = Path('\\\\?\\' + str((base / name).resolve())).read_bytes()
        if label == 'vendor':
            assert digest(raw) == expected[name], name
        target = out / 'source-evidence' / label / name
        target.parent.mkdir(parents=True, exist_ok=True)
        assert not target.exists()
        target.write_bytes(raw)
        sources[target.relative_to(out).as_posix()] = {'original_path': str(base / name),
            'bytes': len(raw), 'sha256': digest(raw), 'declared_vendor_hash_matches': label == 'vendor'}
binary = (checkout / 'build-idf/codex_desk_meter.bin').read_bytes()
elf = checkout / 'build-idf/codex_desk_meter.elf'
assert digest(binary) == '3af7fd933b743ea7b16ba02627617e3adb3be0d5273eb9deb184f1be9c9d51d6'
elf_sha = digest(elf.read_bytes())
assert elf_sha.startswith('5a5fd3f3a'), 'Boot log ELF identity mismatch'
board = (checkout / 'main/board_lcd.c').read_text(encoding='utf-8')
driver = (vendor / '09_FactoryProgram/managed_components/espressif__esp_lcd_st7701/esp_lcd_st7701_rgb.c').read_text(encoding='utf-8')
assert 'vendor.flags.enable_io_multiplex = 1;' in board
assert board.index('esp_lcd_new_panel_st7701(io, &config, &panel)') < board.index('esp_lcd_panel_reset(panel)') < board.index('esp_lcd_panel_init(panel)')
assert 'st7701->io = NULL;' in driver and 'if (!st7701->flags.enable_io_multiplex)' in driver
reset = driver[driver.index('static esp_err_t panel_st7701_reset(esp_lcd_panel_t *panel)\n{'):]
assert reset.index('if (st7701->reset_gpio_num >= 0)') < reset.index('st7701->reset(panel)')
ninja = (checkout / 'build-idf/build.ninja').read_text(encoding='utf-8')
lines = [line for line in ninja.splitlines() if line.startswith('build ') and 'esp_lcd_st7701_rgb.c.obj:' in line]
assert len(lines) == 1 and 'C$:/Espressif/vendor/' in lines[0]
(out / 'vendor-build-binding.txt').write_text(lines[0] + '\n', encoding='utf-8')
objdump = 'C:/Espressif/tools/xtensa-esp-elf/esp-13.2.0_20240530/xtensa-esp-elf/bin/xtensa-esp32s3-elf-objdump.exe'
for function in ['board_lcd_init', 'esp_lcd_new_panel_st7701_rgb', 'panel_st7701_reset', 'panel_st7701_init']:
    result = subprocess.run([objdump, '-d', '--disassemble=' + function, str(elf)], capture_output=True, check=True)
    assert ('<' + function + '>:').encode() in result.stdout
    (out / ('elf-' + function + '.txt')).write_bytes(result.stdout)
    assert not result.stderr
boot = (out / 'hard-reset-serial.bin').read_bytes()
assert b'SPI_FAST_FLASH_BOOT' in boot and b'SPI SRAM memory test OK' in boot and b'USB Serial/JTAG receiver ready' in boot
assert b'Guru Meditation' not in boot and b'abort()' not in boot
accepted = (out / 'post-reset-reference-capture/device-serial.bin').read_bytes()
assert re.search(rb'meter_app: accepted cdm/1 frame sequence=0', accepted)
record = {'run_id': run.name, 'reviewed_at': datetime.now(timezone.utc).isoformat(),
          'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=checkout).decode().strip(),
          'app_sha256': digest(binary), 'elf_sha256': elf_sha, 'sources': sources,
          'static_checks_passed': True, 'compiled_driver_binding_verified': True,
          'boot_observed': True, 'psram_memory_test_observed': True,
          'usb_receiver_ready_observed': True, 'accepted_sequence_observed_in_first_diagnostic_capture': [0],
          'limits': 'No panel register readback, GPIO waveform measurement, modified firmware A/B test or proof of frame1 receipt.'}
(out / 'source-review.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(out / 'comparison-state-before-diagnosis.json').write_bytes(subprocess.check_output(['git', 'show', '3674d26:results/formal-comparison-20261004/progress.json'], cwd=root))
print(json.dumps({key: value for key, value in record.items() if key != 'sources'}))

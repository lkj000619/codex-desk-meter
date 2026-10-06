"""Compile, link and run C/C++ fixtures using the declared host build workflow."""
import json
from pathlib import Path
import subprocess
import tempfile


def main():
    records = []
    with tempfile.TemporaryDirectory(prefix="meter-host-preflight-") as temp:
        root = Path(temp)
        (root / "CMakeLists.txt").write_text('''cmake_minimum_required(VERSION 3.16)
project(host_preflight C CXX)
add_executable(c_runtime main.c)
add_executable(cxx_runtime main.cpp)
enable_testing()
add_test(NAME c_runtime COMMAND c_runtime)
add_test(NAME cxx_runtime COMMAND cxx_runtime)
''')
        (root / "main.c").write_text('''#include <stdio.h>
#include <stdint.h>
#include <string.h>
int main(void) { char b[32]; uint32_t n=123456789u;
snprintf(b,sizeof b,"%u",(unsigned)n);
return strcmp(b,"123456789") != 0; }
''')
        (root / "main.cpp").write_text('''#include <string>
#include <vector>
int main() { std::vector<int> v{1,2,3};
return std::to_string(v.at(2)) != "3"; }
''')
        for argv in (["cmake", "-S", ".", "-B", "build-host", "-G", "Ninja"],
                     ["cmake", "--build", "build-host"],
                     ["ctest", "--test-dir", "build-host", "--output-on-failure"]):
            result = subprocess.run(argv, cwd=root, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=120)
            records.append({"argv": argv, "exit_code": result.returncode,
                            "stdout": result.stdout, "stderr": result.stderr})
            if result.returncode:
                print(json.dumps({"status": "fail", "commands": records}))
                return 1
        print(json.dumps({"status": "pass", "commands": records}))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

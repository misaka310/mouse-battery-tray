from __future__ import annotations

import unittest

from fuzzing.packet_fuzzer import fuzz_one_input


class FuzzTargetTests(unittest.TestCase):
    def test_packet_fuzzer_accepts_arbitrary_bytes_without_crashing(self) -> None:
        samples = [
            b"",
            b"\x03\xb1\x40\x00\x64",
            b"\x03\x85\x40\x02\x0a",
            b"\x03\x85\x40\x02\xff",
            b"\x00" * 64,
            bytes(range(64)),
        ]
        for sample in samples:
            with self.subTest(sample=sample):
                fuzz_one_input(sample)


if __name__ == "__main__":
    unittest.main()

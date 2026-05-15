import io
import sys
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ui import runtime
from ui import scanner
from models.registry import architecture_for_config, get_architectures


class UploadStub:
    def __init__(self, name: str, data: bytes):
        self.name = name
        self._data = data

    def getbuffer(self):
        return memoryview(self._data)

    def read(self, *args, **kwargs):
        return self._data

    def seek(self, *_args):
        return None


def make_zip(entries: dict[str, bytes]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return buf.getvalue()


class RuntimeHelperTest(unittest.TestCase):
    def test_safe_extract_zip_rejects_path_traversal(self):
        with self._temporary_upload_dir() as tmp_path:
            upload = UploadStub("bad.zip", make_zip({"../escape.txt": b"nope"}))

            with self.assertRaisesRegex(ValueError, "非法路径"):
                runtime.safe_extract_zip(upload, "datasets_extracted", prefix="inf_")

            self.assertFalse((tmp_path / "escape.txt").exists())

    def test_safe_extract_zip_uses_content_fingerprint_for_same_filename(self):
        with self._temporary_upload_dir():
            first = UploadStub("images.zip", make_zip({"a.txt": b"one"}))
            second = UploadStub("images.zip", make_zip({"a.txt": b"two"}))

            first_dir = runtime.safe_extract_zip(first, "datasets_extracted", prefix="inf_")
            second_dir = runtime.safe_extract_zip(second, "datasets_extracted", prefix="inf_")

            self.assertNotEqual(first_dir, second_dir)
            self.assertEqual((first_dir / "a.txt").read_bytes(), b"one")
            self.assertEqual((second_dir / "a.txt").read_bytes(), b"two")

    def test_json_download_uses_utf8_and_requested_filename(self):
        prepared = runtime.json_download({"状态": "完成"}, "report.json")

        self.assertEqual(prepared.file_name, "report.json")
        self.assertEqual(prepared.mime, "application/json")
        self.assertNotIn(b"\\u72b6\\u6001", prepared.data)

    def test_save_uploaded_file_uses_content_fingerprint(self):
        with self._temporary_upload_dir_for(scanner) as tmp_path:
            first = UploadStub("best.pt", b"first")
            second = UploadStub("best.pt", b"second")

            first_path = Path(scanner.save_uploaded_file(first, "models"))
            second_path = Path(scanner.save_uploaded_file(second, "models"))
            repeat_path = Path(scanner.save_uploaded_file(first, "models"))

            self.assertNotEqual(first_path, second_path)
            self.assertEqual(first_path, repeat_path)
            self.assertTrue(first_path.name.startswith("best_"))
            self.assertEqual(first_path.suffix, ".pt")
            self.assertEqual(first_path.read_bytes(), b"first")
            self.assertEqual(second_path.read_bytes(), b"second")
            self.assertTrue(first_path.is_relative_to(tmp_path))

    def test_registered_architectures_have_default_configs(self):
        architectures = get_architectures()

        self.assertGreaterEqual(len(architectures), 2)
        for arch in architectures:
            config_path = Path(__file__).resolve().parents[1] / arch.default_config
            self.assertTrue(config_path.exists(), arch.default_config)
            self.assertEqual(architecture_for_config(config_path), arch)

    def _temporary_upload_dir(self):
        import tempfile

        class _Context:
            def __enter__(_self):
                _self.tmp = tempfile.TemporaryDirectory()
                _self.patch = patch.object(runtime, "UPLOAD_DIR", runtime.Path(_self.tmp.name))
                tmp_path = _self.patch.__enter__()
                return tmp_path

            def __exit__(_self, exc_type, exc, tb):
                _self.patch.__exit__(exc_type, exc, tb)
                _self.tmp.cleanup()

        return _Context()

    def _temporary_upload_dir_for(self, module):
        import tempfile

        class _Context:
            def __enter__(_self):
                _self.tmp = tempfile.TemporaryDirectory()
                _self.patch = patch.object(module, "UPLOAD_DIR", module.Path(_self.tmp.name))
                tmp_path = _self.patch.__enter__()
                return tmp_path

            def __exit__(_self, exc_type, exc, tb):
                _self.patch.__exit__(exc_type, exc, tb)
                _self.tmp.cleanup()

        return _Context()


if __name__ == "__main__":
    unittest.main()

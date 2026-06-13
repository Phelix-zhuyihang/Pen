import os
import tempfile
import pytest
from pen.utils import validate_slug, read_file_text


class TestValidateSlug:
    def test_valid_slugs(self):
        assert validate_slug("abc") == (True, "")
        assert validate_slug("hello-world") == (True, "")
        assert validate_slug("test_123") == (True, "")
        assert validate_slug("a" * 48) == (True, "")

    def test_too_short(self):
        ok, msg = validate_slug("ab")
        assert ok is False
        assert "3-48" in msg

    def test_too_long(self):
        ok, msg = validate_slug("a" * 49)
        assert ok is False
        assert "3-48" in msg

    def test_invalid_chars_uppercase(self):
        ok, msg = validate_slug("Hello")
        assert ok is False
        assert "a-z" in msg

    def test_invalid_chars_space(self):
        ok, msg = validate_slug("test space")
        assert ok is False

    def test_invalid_chars_dot(self):
        ok, msg = validate_slug("test.123")
        assert ok is False

    def test_empty_string(self):
        ok, msg = validate_slug("")
        assert ok is False


class TestReadFileText:
    def test_read_utf8(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("hello world")
            path = f.name
        try:
            result = read_file_text(path)
            assert result == "hello world"
        finally:
            os.unlink(path)

    def test_read_chinese(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("你好世界")
            path = f.name
        try:
            result = read_file_text(path)
            assert result == "你好世界"
        finally:
            os.unlink(path)

    def test_binary_extension_rejected(self):
        with pytest.raises(ValueError, match="二进制文件"):
            read_file_text("test.png")

    def test_binary_content_rejected(self):
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            f.write(b"\x00" * 100 + b"text")
            path = f.name
        try:
            with pytest.raises(ValueError, match="二进制文件"):
                read_file_text(path)
        finally:
            os.unlink(path)

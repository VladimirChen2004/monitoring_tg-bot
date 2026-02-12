import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.checks.base import CheckStatus
from bot.checks.file_check import FileCheck
from bot.checks.gpu_check import GPUCheck
from bot.checks.http_check import HTTPHealthCheck
from bot.checks.subprocess_check import SubprocessCheck


@pytest.mark.asyncio
async def test_http_check_ok():
    with patch("bot.checks.http_check.aiohttp.ClientSession") as mock_session_cls:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.text = AsyncMock(return_value='{"data":[]}')
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        mock_session_cls.return_value = mock_session

        check = HTTPHealthCheck(name="test", url="http://localhost:8001/v1/models")
        result = await check.execute()
        assert result.status == CheckStatus.OK
        assert "200" in result.message


@pytest.mark.asyncio
async def test_subprocess_check_ok():
    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(return_value=(b"claude-code 1.0.0\n", b""))
    mock_proc.returncode = 0

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        check = SubprocessCheck(name="Claude CLI", command=["claude", "--version"])
        result = await check.execute()
        assert result.status == CheckStatus.OK
        assert "claude-code" in result.message


@pytest.mark.asyncio
async def test_subprocess_check_not_found():
    with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
        check = SubprocessCheck(name="missing", command=["nonexistent"])
        result = await check.execute()
        assert result.status == CheckStatus.CRITICAL
        assert "not found" in result.message


@pytest.mark.asyncio
async def test_file_check_no_file(tmp_path):
    check = FileCheck(name="lock", path=str(tmp_path / "nonexistent.lock"))
    result = await check.execute()
    assert result.status == CheckStatus.OK
    assert "Not running" in result.message


@pytest.mark.asyncio
async def test_file_check_exists(tmp_path):
    lock = tmp_path / "test.lock"
    lock.write_text("locked")
    check = FileCheck(name="lock", path=str(lock))
    result = await check.execute()
    assert result.status == CheckStatus.OK
    assert "Running" in result.message


@pytest.mark.asyncio
async def test_gpu_check_no_nvidia():
    with patch("asyncio.create_subprocess_exec", side_effect=FileNotFoundError):
        check = GPUCheck()
        result = await check.execute()
        assert result.status == CheckStatus.UNKNOWN
        assert "not found" in result.message


@pytest.mark.asyncio
async def test_gpu_check_parses_output():
    nvidia_output = b"0, NVIDIA A100, 34, 8192, 81920, 52\n"
    mock_proc = AsyncMock()
    mock_proc.communicate = AsyncMock(return_value=(nvidia_output, b""))
    mock_proc.returncode = 0

    with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
        check = GPUCheck()
        result = await check.execute()
        assert result.status == CheckStatus.OK
        assert result.details["gpus"][0]["utilization"] == 34
        assert result.details["gpus"][0]["temperature"] == 52

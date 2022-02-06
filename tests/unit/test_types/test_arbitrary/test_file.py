import io
import pathlib
from typing import Any, Callable, Generator

import pytest
from _pytest.fixtures import SubRequest


# spike for mypy
from glQiwiApi.types.types.arbitrary import PlainPathInput, PathlibPathInput, BinaryIOInput, File

lazy_fixture: Callable[..., Any] = pytest.lazy_fixture  # type: ignore  # noqa


@pytest.fixture()
def path_to_test_file(tmpdir_factory: pytest.TempdirFactory) -> pathlib.Path:
    path = pathlib.Path(tmpdir_factory.mktemp("data").join("test.txt"))
    with path.open("wb") as f:
        f.write(b"test")
    return path


@pytest.fixture()
def plain_path_input(path_to_test_file: pathlib.Path) -> PlainPathInput:
    return PlainPathInput(path_to_test_file.__str__())


@pytest.fixture()
def pathlib_input(path_to_test_file: pathlib.Path) -> PathlibPathInput:
    return PathlibPathInput(path_to_test_file)


@pytest.fixture()
def binary_io_input(path_to_test_file: pathlib.Path) -> Generator[BinaryIOInput, None, None]:
    opened_file = path_to_test_file.open("wb+")
    yield BinaryIOInput(opened_file)
    opened_file.close()


@pytest.fixture()
def file(request: SubRequest) -> File:
    return File(input=request.param)


@pytest.mark.parametrize(
    "file",
    [
        lazy_fixture("plain_path_input"),
        lazy_fixture("pathlib_input"),
    ],
    indirect=True,
)
def test_get_filename(file: File, path_to_test_file: pathlib.Path) -> None:
    filename = file.get_filename()
    assert filename == path_to_test_file.name


@pytest.mark.parametrize("file", [lazy_fixture("binary_io_input")], indirect=True)
def test_fail_to_get_filename_cause_binary_input(file: File) -> None:
    with pytest.raises(TypeError):
        file.get_filename()


@pytest.mark.parametrize(
    "file",
    [
        lazy_fixture("plain_path_input"),
        lazy_fixture("pathlib_input"),
    ],
    indirect=True,
)
def test_get_path(file: File) -> None:
    path = file.get_path()
    assert isinstance(path, str) is True


@pytest.mark.parametrize("file", [lazy_fixture("binary_io_input")], indirect=True)
def test_fail_to_get_path_cause_input_is_binary(file: File) -> None:
    with pytest.raises(TypeError):
        file.get_path()


@pytest.mark.parametrize(
    "file",
    [
        lazy_fixture("plain_path_input"),
        lazy_fixture("pathlib_input"),
        lazy_fixture("binary_io_input"),
    ],
    indirect=True,
)
def test_get_binary(file: File) -> None:
    stream = file.get_underlying_file_descriptor()
    assert isinstance(stream, io.IOBase) is True


@pytest.mark.parametrize(
    "file",
    [
        lazy_fixture("plain_path_input"),
        lazy_fixture("pathlib_input"),
        lazy_fixture("binary_io_input"),
    ],
    indirect=True,
)
def test_save(file: File, path_to_test_file: pathlib.Path) -> None:
    file.save(path_to_test_file)
    assert path_to_test_file.is_file()


@pytest.mark.parametrize(
    "file",
    [
        lazy_fixture("plain_path_input"),
        lazy_fixture("pathlib_input"),
        lazy_fixture("binary_io_input"),
    ],
    indirect=True,
)
@pytest.mark.asyncio
async def test_asynchronously(file: File, path_to_test_file: pathlib.Path) -> None:
    await file.save_asynchronously(path_to_test_file)
    assert path_to_test_file.is_file()

"""Functions for writing data to disk."""
import logging
from os import path, remove, PathLike, makedirs
from pathlib import Path

from quaker.core.query import Query
from quaker.globals import STDOUT

# TODO Test Writer
# - [ ] __init__
# - [ ] cleanup
# - [ ] write_lines
# TODO Test JsonWriter
# - [ ] __new__ resolution
# - [ ] line joins

logger = logging.getLogger(__name__)

class Writer:
    def __new__(cls, _output_file, query):
        if query.format == 'geojson':
            return super().__new__(JsonWriter)
        return super().__new__(cls)

    def __init__(self, output_file: PathLike, _query: Query):
        self.output_file = self._validate_output_file(output_file)

    @staticmethod
    def _validate_output_file(output_file: PathLike) -> PathLike:
        if output_file == STDOUT:
            return output_file

        output_file = path.abspath(output_file)
        if path.exists(output_file):
            raise FileExistsError("File exists, remove the file or select a different destination.")

        parent_dir, _ = path.split(output_file)
        if not path.exists(parent_dir):
            logger.info(f"Directory {parent_dir} doesnt exist, creating.")
            makedirs(parent_dir, exist_ok=True)

        # TODO upgrade to pathlib
        Path(output_file).touch()
        return output_file

    def cleanup_output(self):
        # TODO pathlib
        if self.output_file != STDOUT and path.exists(self.output_file):
            remove(self.output_file)

    def write_lines(self, lines):
        if len(lines) == 0:
            logger.warning("Empty list of lines recieved")
            return

        error_recived = None
        with open(self.output_file, "a", encoding="utf-8") as f:
            try:
                f.writelines(f"{l}\n" for l in lines)
            except KeyboardInterrupt:
                logger.error("Keyboard interrupt recieved, safely closing file.")
            except Exception as error:  # pylint: disable=broad-except
                logger.error("Unknown error recieved, safely closing file.")
                error_recived = error

        if error_recived is not None:  # Signal to process that keyboard interrupt was received.
            raise error_recived

    def __call__(self, lines):
        self.write_lines(lines)

class JsonWriter(Writer):
    def __call__(self, lines):
        if len(lines) <= 2:
            self.write_lines(["".join(lines)])
            return

        if len(lines) > 3: # more than one record, header and footer
            # Append commas to all records except last one
            for i in range(1, len(lines) - 2):
                lines[i] += ","

        # join header onto first record
        lines[1] = lines[0] + lines[1]

        # join footer onto last record
        lines[-2] = lines[-2] + lines[-1]

        self.write_lines(lines[1:-1])

from pathlib import Path
import os
import re
from .ReplacerTool import ReplacerTool
from .instructions import *
from typing import Union, Optional, Callable
from jumpscale.god import j


class CodeFixer:
    def __init__(self):
        self._init_ = False

    def _init(self):
        if not self._init_:
            self._replacer_method = ReplacerTool(instructions_method_replace)
            self._replacer_word = ReplacerTool(instructions_word_replace)
            self._replacer_obj = ReplacerTool(instructions_obj_part_replace)
            self._init_ = True

            self._replacer_method.do("s")

    def fix(self, path: Optional[Path] = None):
        """
        jsng 'j.tools.codefixer.fix()'
        Args:
            path:

        Returns:

        """
        self._init()
        self.walk(file_method=self._fix_file, path=path)

    def _fix_file(self, path: Path):
        """
        see if file is relevant is yes walk over it line by line

        Args:
            path:

        Returns:

        """
        if path.name.find("CodeUpdater") != -1:
            return
        if "." not in path.name:
            return
        if not path.suffix in ["py", "md", "txt"]:
            return
        content0 = path.read_text()
        content1=None
        for i in range(3):
            content1 = self._fix_content(content0, path=path)
        if content1.strip()!= content0.strip():
            j.shell()
            # path.write_text(content1)

    def _fix_content(self, content: str, path: Path) -> str:
        out = ""
        for line in content.split("\n"):
            out += "%s\n" % self._fix_line(line, path=path)
        return out

    def _fix_line(self, line: str, path: Path) -> str:
        """

        Args:
            line: the line which will be processed for the multiple steps

        Returns:

        """

        line = self._replacer_word.do(line)

        # find obj parts e.g. j.exceptions
        line = self._regex_process(r"[\.\w]+\.", line, self._replacer_obj.do, path=path)
        # check for methods
        line = self._regex_process(r"[\.\w\-]+\(", line, self._replacer_method.do, path=path)

        return line

    def _regex_process(self, regex: str, line: str, method: Callable, path: Path) -> str:
        """
        see if we can find a regex on the line and for each match run the method

        method is called as method(matched_string,path_object)
        """
        for m in re.finditer(regex, line):
            foundstr = m.string[m.start() : m.end()]
            result_str = method(foundstr, path=path)
            line = line.replace(foundstr, result_str)
        return line

    def walk(self, path: Optional[Path] = None, file_method: Optional[Callable] = None):

        if not path:
            path = Path(os.getcwd())

        if not file_method:
            file_method = self._fix_file

        p = Path(path)
        for dpath in p.iterdir():
            if dpath.name.startswith("."):
                continue
            if dpath.name.startswith("_"):
                continue
            dpath.absolute()
            if dpath.is_dir():
                self.walk(path=dpath, file_method=file_method)
            elif dpath.is_symlink():
                continue
            elif dpath.is_file():
                file_method(dpath)

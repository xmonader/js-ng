from typing import Union, Optional, List, Callable
from jumpscale.god import j
from pathlib import Path

class ReplacerToolBaseItem:
    """
    has the knowledge how to replace code fragments based on an instructions file e.g. instructions_word_replace

    an instruction file is format

    ```
    $tofind
    $tofind : $replacewith

    the replacer tool only works on 1 line of the instruction file

    ```

    """

    pass


class ReplaceItem(ReplacerToolBaseItem):
    def __init__(self, left: str, right: Optional[str] = None):
        self.left = left.strip()
        if self.left.startswith("||"):
            # is a regex
            self.regex = True
        else:
            self.regex = False
        # makes camelcase, snakecase
        if not right:
            right = ""
            for char in left:
                if char != char.lower():
                    char = "_%s" % char.lower()
                right += char
        self.right = right.strip()

    def replace(self, txt: str) -> str:
        if self.regex:
            # TODO: need to implement regex support
            raise j.exceptions.Base("implement")
        else:
            if txt.find(self.left) != -1:
                txt = txt.replace(self.left, self.right)
        return txt

    def __str__(self):
        return "%-40s: %s" % (self.left, self.right)

    __repr__ = __str__


class ReplacerTool:
    def __init__(self, instruction_str: str):
        self._read_instructions(instruction_str)
        self._instructions: List[ReplaceItem] = []

    def do(self,text:str,path:Optional[Path]=None):
        for instruction in self._instructions:
            text=instruction.replace(text)
        return text

    def _read_instructions(self, config: str, replacer: Optional[Callable] = None):
        """

        Args:
            config:

        Returns:

        """
        right: Optional[str] = None
        for line in config.split("\n"):
            if line.strip() == "":
                continue
            if line.strip().startswith("#"):
                continue
            if ":" in line:
                left, right = line.split(":", 1)
            else:
                left = line
            if not replacer:
                replacer = ReplaceItem
            r = replacer(left=left, right=right)
            self._instructions.append(r)

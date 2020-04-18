"""This module is providing everything needed for decent filesystem management
# Using System Fs

Manipulating filesystem is one of the most common things in the daily life of a developer, administrator, .. etc. js-ng comes with tons of helpers and utilities around that in `j.sals.fs`. You will find the module already self documented with lots of examples in each function.


### Get current working dir

```
> j.sals.fs.cwd()
'/home/xmonader/wspace/js-next/js-ng'
```

### Get basename
```
> j.sals.fs.basename(j.sals.fs.cwd()) 
'js-ng'
```

### Get Dir name
```
> j.sals.fs.dirname(j.sals.fs.cwd())
'/home/xmonader/wspace/js-next'
> j.sals.fs.parent(j.sals.fs.cwd()) 
'/home/xmonader/wspace/js-next'
```

### is dir

```
> j.sals.fs.is_dir(path= '/home/rafy')
True
```
### is file
```
> j.sals.fs.is_file(path= '/home/rafy')
False
```

### is ascii file

```
> j.sals.fs.is_ascii_file(path="/home/rafy/testfile")
True
```

### Is absolute path

```
> j.sals.fs.is_absolute('/home/rafy/')
True
```

### Check if empty dir
```
> j.sals.fs.is_empty_dir("/home/rafy/empty_dir")
True
```

### File paths exists or not

```
> j.sals.fs.exists("/home/rafy/testing_make_dir/test1")
True
```

## Reading/Writing to a file

There're some helpers around reading/writing text, binary like `read_text`, `read_binary`, `read_file`, `write_text`, `write_binary`, `touch`

### Touching a new file

```
> j.sals.fs.touch("/home/rafy/testing_touch")
```

### Reading a text

```
> j.sals.fs.read_text("/home/rafy/testing_text.txt")
'hello world\n'

```

### Reading binary

```
> j.sals.fs.read_bytes("/home/rafy/testing_text.txt")
b'hello world\n'
```


### Writing text

```
> j.sals.fs.write_text(path="/home/rafy/testing_text.txt",data="hello world")
11
```

### Writing binary

```
> j.sals.fs.write_bytes(path="/home/rafy/testing_text.txt",data=b"hello world")
11
```


rename, move, copy_file, copy_tree, mkdir, mkdirs, join_paths, , rmtree, rm_empty_dir, symlink, chmod, chown, basename, dirname, normalizing paths, expanding `~`



### Making directories
```
> j.sals.fs.mkdirs("/home/rafy/testing_make_dir/test1/test2",exist_ok=False)
```
will raise if in case the directory already exists

```
> j.sals.fs.mkdirs("/home/rafy/testing_make_dir/test1/test2",exist_ok=True) 
```
Won't raise if the directory exists

### Get the stem of the filepath

```
> j.sals.fs.stem("/tmp/tmp-5383p1GOmMOOwvfi.tpl") 'tmp-5383p1GOmMOOwvfi'
   
```

### Get the parent 

```
> j.sals.fs.parent("/home/rafy/testing_make_dir/test1")
'/home/rafy/testing_make_dir'
```

### Get parents

```
> j.sals.fs.parents("/tmp/home/ahmed/myfile.py")
    [PosixPath('/tmp/home/ahmed'),
    PosixPath('/tmp/home'),
    PosixPath('/tmp'),
    PosixPath('/')]
```


### Rename file
```
> j.sals.fs.rename("/home/rafy/testing_make_dir","/home/rafy/testing_dir") 
```

### Expand user
```
> j.sals.fs.expanduser("~/work")
'/home/xmonader/work'
```

### Get temporary filename 
```
> j.sals.fs.get_temp_filename(dir="/home/rafy/")  
'/home/rafy/tmp6x7w71ml'
```

```
> j.sals.fs.get_temp_dirname(dir="/home/rafy")  
'/home/rafy/tmpntm2ptqy'
```

```
> j.sals.fs.join_paths("home","rafy")  
'home/rafy'
```

### Resolving a path
```
> j.sals.fs.resolve("")  
PosixPath('/home/rafy/Documents')
> j.sals.fs.resolve("./testing_text.txt")  
PosixPath('/home/rafy/Documents/testing_text.txt')
```

## Walkers
It's very common to walk on the filesystem and filtering based on some properties of the path 
And very fancy walkers

### Walk over on files only

```
for el in walk('/tmp', filter_fun=j.sals.fs.is_file) : ..
```
or more specific function walk_files

```
for el in walk_files('/tmp') : ..
```



### Walk over on dirs only

```
for el in walk('/tmp', filter_fun=j.sals.fs.is_dir) : ..
```
or more specific function `walk_dirs`

```
for el in walk_dirs('/tmp') : ..

```

### walk over with a bit complex filter

 Walk over paths that are files or dirs and longer than 4 characters in the name

```
for el in walk('/tmp', filter_fun= lambda x: len(x)>4 and (j.sals.fs.is_file(x) or j.sals.fs.is_dir(x)) ) : ..
```
   

There are more functionality available in the SAL `j.sals.fs` make sure you check the API documentation for more.

"""

from pathlib import Path
import pathlib
import tempfile
import os
import shutil
import stat
from distutils import dir_util
from typing import List
from typing import Union, Optional, List, Callable
import jumpscale.core.exceptions as err

basename = os.path.basename
dirname = os.path.dirname
common_path = os.path.commonpath
common_prefix = os.path.commonprefix
norm_path = os.path.normpath
norm_case = os.path.normcase
get_access_time = os.path.getatime
get_modified_time = os.path.getmtime
get_creation_time = os.path.getctime
sep = os.path.sep
is_samefile = os.path.samefile
expandvars = os.path.expandvars
expanduser = os.path.expanduser
realpath = os.path.realpath


def home() -> str:
    """Return the home directory
    e.g
        j.sals.fs.home()  -> '/home/rafy'

    Returns:
        str: home directory.
    """
    return str(pathlib.Path.home())


def cwd() -> str:
    """Return current working directory.
    e.g
        j.sals.fs.cwd()  -> '/home/rafy' 


    Returns:
        str: current directory
    """
    return str(pathlib.Path.cwd())


def is_dir(path:Union[Path,str]) -> bool:
    """Checks if path is a dir
    e.g
        j.sals.fs.is_dir(path= '/home/rafy')  -> True
        j.sals.fs.is_dir(path= '/home/rafy/file.txt')  -> False

    Args:
        path (str): path to check if is directory
    Returns:
        bool: True if is dir and False otherwise
    """
    path = _str_to_path(path)
    return pathlib.Path(path).is_dir()


def is_file(path:Union[Path,str]) -> bool:
    """Checks if path is a file
    e.g
        j.sals.fs.is_file(path= '/home/rafy')  -> False
        j.sals.fs.is_file(path= '/home/rafy/file.txt')  -> True

    Args:
        path (str): path to check if is file

    Returns:
        bool: True if is file and False otherwise
    """
    path = _str_to_path(path)
    return pathlib.Path(path).is_file()


def is_symlink(path:Union[Path,str]) -> bool:
    """Checks if path symlink
    e.g
        j.sals.fs.is_symlink('/home/rafy/testfile3')  -> True
        j.sals.fs.is_symlink('/home/rafy/testfile2')  -> False

    Args:
        path (str): path to check if symlink

    Returns:
        bool: True if symlink False otherwise
    """
    path = _str_to_path(path)
    return pathlib.Path(path).is_symlink()


def is_absolute(path:Union[Path,str]) -> bool:
    """Checks if path is absolute
    e.g
        j.sals.fs.is_absolute('/home/rafy/')  -> True
        j.sals.fs.is_absolute('~/rafy/')  -> False

    Args:
        path (str): path to check if it is absolute 

    Returns:
        bool: True if absolute
    """
    path = _str_to_path(path)
    return pathlib.Path(path).is_absolute()


def is_mount(path:Union[Path,str]) -> bool:
    # TODO add example here
    """Checks if path is mount

    Args:
        path (str): path to check if it is mounded or not

    Returns:
        bool: True if mount
    """
    path = _str_to_path(path)
    return path.is_mount()


def is_ascii_file(path:Union[Path,str], checksize=4096) -> bool:
    """Checks if file `path` is ascii
    e.g
         j.sals.fs.is_ascii_file(path="/home/rafy/testfile")  -> True

    Args:
        path (str): file path
        checksize (int, optional): checksize. Defaults to 4096.

    Returns:
        bool: True if ascii file
    """
    path=_path_to_str(path)
    # TODO: let's talk about checksize feature.
    try:
        with open(path, encoding="ascii") as f:
            f.read()
            return True
    except UnicodeDecodeError:
        return False


def is_empty_dir(path:Union[Path,str]) -> bool:
    """Checks if path is emptry directory
    e.g
        j.sals.fs.is_empty_dir("/home/rafy/empty_dir")  -> True
        j.sals.fs.is_empty_dir("/home/rafy")  -> False

    Args:
        path (str): path to check if empty directory

    Returns:
        bool: True if path is emptry directory
    """
    path = _str_to_path(path)
    try:
        g = path.iterdir()
        next(g)
    except StopIteration:
        # means we can't get next entry -> dir is empty.
        return True
    else:
        return False


is_binary_file = lambda path: not is_ascii_file(path)


def is_broken_link(path:Union[Path,str], clean=False) -> bool:
    """Checks if path is a broken symlink

    Args:
        path (str): path to check
        clean (bool, optional): remove symlink if broken. Defaults to False.

    Raises:
        NotImplementedError: [description]

    Returns:
        bool: True if path is a broken symlink
    """
    raise err.NotImplemented("implement")


def _str_to_path(path:Union[Path,str],needexist:bool=False)->Path:
    if isinstance(path,str):
        path=Path(path)
    if needexist:
        exists_required(path=path)
    return path

def _path_to_str(path:Union[Path,str],needexist:bool=False):
    if not isinstance(path,str):
        path=path.as_posix()
    if needexist:
        exists_required(path)
    return path

def exists_required(path:Union[Path,str])->None:
    path=_str_to_path(path)
    if not path.exists():
        raise err.Operations(f"Path:'{path.as_posix()}' does not exist.")


def stem(path: Union[Path,str]) -> str:
    """returns the stem of a path (path without parent directory and without extension)
    e.g
        j.sals.fs.stem("/tmp/tmp-5383p1GOmMOOwvfi.tpl")  -> 'tmp-5383p1GOmMOOwvfi'

    Args:
        path (str): path we want to get its stem

    Returns:
        str: path without parent directory and without extension
    """
    path = _str_to_path(path)
    return pathlib.Path(path).stem


def mkdir(path:Union[Path,str], exist_ok=True):
    """Makes directory at path
    e.g 
        j.sals.fs.mkdir("/home/rafy/testing_make_dir")
        j.sals.fs.mkdir("/home/rafy/testing_make_dir",exist_ok=True)
        j.sals.fs.mkdir("/home/rafy/testing_make_dir",exist_ok=False) -> File exists: '/home/rafy/testing_make_dir' (raise exception as the file exist and  exist_ok flag is false)
        
    Args:
        path (str): path to create dir at
        exist_ok (bool, optional): won't fail if directory exists. Defaults to True.

    Returns:
        [type]: [description]
    """
    path = _str_to_path(path)
    return path.mkdir(exist_ok=exist_ok)


def mkdirs(path:Union[Path,str], exist_ok=True):
    """Creates dir as well as all non exisitng parents in the path
    e.g
        j.sals.fs.mkdirs("/home/rafy/testing_make_dir/test1/test2",exist_ok=False) 
        j.sals.fs.mkdirs("/home/rafy/testing_make_dir/test1/test2",exist_ok=True) 
        j.sals.fs.mkdirs("/home/rafy/testing_make_dir/test1/test2",exist_ok=False)  -> File exists: '/home/rafy/testing_make_dir/test1/test2'(raise exception as the file exist and  exist_ok flag is false)

    Args:
        path (str): path to create dir at
        exist_ok (bool, optional): won't fail if directory exists. Defaults to True.
    """
    path = _path_to_str(path)
    return os.makedirs(path, exist_ok=exist_ok)


def parent(path:Union[Path,str]) -> str:
    """Get path's parent
    e.g 
        j.sals.fs.parent("/home/rafy/testing_make_dir/test1")  -> '/home/rafy/testing_make_dir'
    
    Args:
        path (str): path to get its parent

    Returns:
        str: parent path.
    """
    path=_str_to_path(path)
    return str(pathlib.Path(path).parent)


def parents(path:Union[Path,str]) -> List[str]:
    """Get parents list

    e.g
        j.sals.fs.parents("/tmp/home/ahmed/myfile.py") -> 
    [PosixPath('/tmp/home/ahmed'),
    PosixPath('/tmp/home'),
    PosixPath('/tmp'),
    PosixPath('/')]

    Args:
        path (str): path to get its parents

    Returns:
        List[str]: list of parents
    """
    path=_str_to_path(path)
    return list([str(p) for p in pathlib.Path(path).parents])


def path_parts(path:Union[Path,str]):
    """Convert path to a list of parts
    e.g
        '/tmp/tmp-5383p1GOmMOOwvfi.tpl' ->  ('/', 'tmp', 'tmp-5383p1GOmMOOwvfi.tpl')
    Args:
        path (str): path to convert to parts

    Returns:
        List[str]: path parts.
    """
    path=_str_to_path(path)
    return path.parts


def exists(path:Union[Path,str]) -> bool:
    """Checks if path exists
    e.g
        j.sals.fs.exists("/home/rafy/testing_make_dir/test1")  -> True
        j.sals.fs.exists("/home/rafy/testing_make_dir/fasdljd")  -> False

    Args:
        path (str): path to check for existence

    Returns:
        bool: True if exists
    """
    path=_str_to_path(path)
    return path.exists()


def rename(path1: Union[Path,str], path2: Union[Path,str]):
    """Rename path1 to path2
    e.g
        j.sals.fs.rename("/home/rafy/testing_make_dir","/home/rafy/testing_dir") 

    Args:
        path1 (str): source path
        path2 (str): dest path

    """
    path1=_str_to_path(path1)
    path2=_str_to_path(path2)
    return path.rename(path2)


def expanduser(path:Union[Path,str]) -> str:
    """Expands the tilde `~` to username
    e.g
        j.sals.fs.expanduser("~/work") -> '/home/xmonader/work'
    Args:
        path (str): path with optionally `~`

    Returns:
        str: path with tilde `~` resolved.
    """
    path=_str_to_path(path,needexist=True)
    return str(path.expanduser())


def unlink(path:Union[Path,str]):
    """unlink path
    e.g 
        j.sals.fs.unlink("/home/rafy/testfile3")
    Args:
        path (str): path to unlink
    """
    path=_str_to_path(path)
    return path.unlink()


def read_text(path:Union[Path,str]) -> str:
    """read ascii content at `path`
    e.g
        j.sals.fs.read_text("/home/rafy/testing_text.txt")  -> 'hello world\n'

    Args:
        path (str): ascii file path

    Returns:
        str: ascii content in path
    """
    path=_str_to_path(path,needexist=True)
    return path.read_text()


read_ascii = read_file = read_text


def read_bytes(path:Union[Path,str]) -> bytes:
    """read binary content at `path`
    e.g
        j.sals.fs.read_bytes("/home/rafy/testing_text.txt")  -> b'hello world\n'

    Args:
        path (str): binary file path

    Returns:
        bytes: binary content in path
    """
    path=_str_to_path(path,needexist=True)
    return path.read_bytes()


read_binary = read_file_binary = read_bytes


def write_text(path:Union[Path,str], data: str, encoding=None):
    """write text `data` to path `path` with encoding
    e.g
        j.sals.fs.write_text(path="/home/rafy/testing_text.txt",data="hello world")  -> 11

    Args:
        path (str): path to write to
        data (str): ascii content
        encoding ([type], optional): encoding. Defaults to None.

    Returns:
        int: Return the decoded contents of the pointed-to file as a string

    """
    path=_str_to_path(path)
    return path.write_text(data, encoding)


write_ascii = write_file = write_text


def write_bytes(path:Union[Path,str], data: bytes):
    """write binary `data` to path `path`
    e.g
        j.sals.fs.write_bytes(path="/home/rafy/testing_text.txt",data=b"hello world")  -> 11

    Args:
        path (str): path to write to
        data (bytes): binary content
    
    Returns:
        int: Return the binary contents of the pointed-to file as a bytes object 
    """
    path=_str_to_path(path)
    return path.write_bytes(data)


write_binary = write_file_binary = write_bytes


def touch(path:Union[Path,str]):
    """create file
    e.g
        j.sals.fs.touch("/home/rafy/testing_touch")

    Args:
        path (str): path to create file

    """
    path=_str_to_path(path)
    return path.touch()


def get_temp_filename(mode="w+b", buffering=-1, encoding=None, newline=None, suffix=None, prefix=None, dir=None) -> str:
    """Get temp filename
    e.g
        j.sals.fs.get_temp_filename(dir="/home/rafy/")  -> '/home/rafy/tmp6x7w71ml'

    Args:
        mode (str, optional): [description]. Defaults to "w+b".
        buffering (int, optional): buffering. Defaults to -1.
        encoding ([type], optional): encoding . Defaults to None.
        newline ([type], optional):  Defaults to None.
        suffix ([type], optional): ending suffix. Defaults to None.
        prefix ([type], optional): prefix . Defaults to None.
        dir ([type], optional): where to create the file. Defaults to None.

    Returns:
        [str]: temp filename
    """
    return tempfile.NamedTemporaryFile(mode, buffering, encoding, newline, suffix, prefix, dir).name


def get_temp_dirname(suffix=None, prefix=None, dir=None) -> str:
    """Get temp directory name
    e.g
        j.sals.fs.get_temp_dirname(dir="/home/rafy")  -> '/home/rafy/tmpntm2ptqy'

    Args:
        suffix ([type], optional): ending suffix. Defaults to None.
        prefix ([type], optional): prefix . Defaults to None.
        dir ([type], optional): where to create the directory. Defaults to None.


    Returns:
        str: temp directory name.
    """
    return tempfile.TemporaryDirectory(suffix, prefix, dir).name


NamedTemporaryFile = tempfile.NamedTemporaryFile
TempraryDirectory = tempfile.TemporaryDirectory
mkdtemp = tempfile.mkdtemp
mkstemp = tempfile.mkstemp
get_temp_dir = tempfile.gettempdir


def parts_to_path(parts: List[str]) -> str:
    """Convert list of path parts into a path string
    e.g
        j.sals.fs.parts_to_path(["home","rafy"])  -> 'home/rafy'
    
    Args:
        parts (List[str]): path parts

    Returns:
        str: joined path parts
    """
    path = pathlib.Path(parts[0])
    for p in parts[1:]:
        path = path.joinpath(p)
    return str(path)


def join_paths(*paths) -> str:
    """
    Convert tuple of path parts into a path string
    e.g
        j.sals.fs.join_paths("home","rafy")  -> 'home/rafy' 

    Args:
        parts (tuple): path parts (path parts comma seprated and they will be used as a tuple)

    Returns:
        str: joined path parts

    """

    return parts_to_path(paths)


def delete(path: Union[str,Path]):
    """
    Remove dir, link or file
    e.g
    j.sals.fs.delete("/home/rafy/empty_dir")   

    Args:
        path (str,Path): path to remove.

    """
    path=_str_to_path(path)
    if path.is_file() or path.is_symlink():
        os.remove(path.as_posix())
    elif path.is_dir():
        path.rmdir()
        # shutil.rmtree(path)
    else:
        raise err.Base("unsupported type")

def copy_stat(src: Union[str,Path], dst: Union[str,Path], times=True, perms=True):
    """Copy stat of src to dst

    Args:
        src (str): source path
        dst (str): destination
        times (bool, optional):  Defaults to True.
        perms (bool, optional): permissions Defaults to True.
    """
    src=_str_to_path(src,needexist=True)
    dst=_str_to_path(dst)
    st = os.stat(src)
    if hasattr(os, "utime"):
        os.utime(dst, (st.st_atime, st.st_mtime))
    if hasattr(os, "chmod"):
        m = stat.S_IMODE(st.st_mode)
        os.chmod(dst, m)


def copy_file(src: Union[str,Path], dst: Union[str,Path], times=False, perms=False):
    """Copy the file, optionally copying the permission bits (mode) and
        last access/modify time. If the destination file exists, it will be
        replaced. Raises OSError if the destination is a directory. If the
        platform does not have the ability to set the permission or times,
        ignore it.
        This is shutil.copyfile plus bits of shutil.copymode and
        shutil.copystat's implementation.
        shutil.copy and shutil.copy2 are not supported but are easy to do.
    e.g
        j.sals.fs.copy_file(src="/home/rafy/testing_text.txt",dst="/home/rafy/Documents/testing_text.txt")

    Args:
        src (str): source path
        dst (str): destination

    """
    src=_path_to_str(src,needexist=True)
    dst=_path_to_str(dst)    
    shutil.copyfile(src, dst)
    if times or perms:
        copy_stat(src, dst, times, perms)


def symlink(src: Union[str,Path], dst: Union[str,Path], overwrite=False):
    """Create a symbolic link.
    e.g
        j.sals.fs.symlink(src="/home/rafy/testing_text.txt",dst="/home/rafy/link_test")

    Args:
        src (str): Source of link
        dst (str): Destination path of link
        overwrite (bool, optional): If link exists will delete it. Defaults to False.
    """
    src=_path_to_str(src,needexist=True)
    dst=_path_to_str(dst)   

    if overwrite and exists(dst):
        os.unlink(dst)

    os.symlink(src, dst)


copy_tree = dir_util.copy_tree
chdir = os.chdir


def change_dir(path:Union[Path,str]) -> str:
    """Change current working directory to `path`
    e.g
         j.sals.fs.change_dir("/home/rafy/Documents")  -> '/home/rafy/Documents'

    Args:
        path (str): path to switch current working directory to

    Returns:
        str: new current working dir
    """
    path=_path_to_str(path,needexist=True)
    os.chdir(path)
    return path


def chmod(path:Union[Path,str], mode):
    """change file mode for path to mode
    e.g
        j.sals.fs.chmod("/home/rafy/testing_dir",777)

    Args:
        path (str): path
        mode (int): file mode

    """
    path=_str_to_path(path,needexist=True)
    return path.chmod(mode)


def lchmod(path:Union[Path,str], mode):
    """change file mode for path to mode (handles links too)

    Args:
        path (str): path
        mode (int): file mode

    """
    path=_str_to_path(path,needexist=True)
    return path.lchmod(mode)


def stat(path:Union[Path,str]):
    """Gets stat of path `path`
    e.g 
        j.sals.fs.stat("/home/rafy/test_dir/test")  -> os.stat_result(st_mode=33204, st_ino=795348, st_dev=2049, st_nlink=1, st_uid=1000, st_gid=1000, st_size=0, st_atime=1586445434, st_mtime=1586445434, st_ctime=1586445434)
    Args:
        path (str): path to get its stat

    Returns:
        stat_result: returns stat struct.
    """
    path=_str_to_path(path,needexist=True)
    return path.stat()


def lstat(path:Union[Path,str]):
    """Gets stat of path `path` (handles links)
    e.g
         j.sals.fs.lstat("/home/rafy/testing_link")  -> os.stat_result(st_mode=41471, st_ino=7081257, st_dev=2049, st_nlink=1, st_uid=1000, st_gid=1000, st_size=16, st_atime=1586445737, st_mtime=1586445734, st_ctime=1586445734)

    Args:
        path (str): path to get its stat

    Returns:
        stat_result: returns stat struct.
    """
    path=_str_to_path(path,needexist=True)
    return path.lstat()



def resolve(path:Union[Path,str]) -> str:
    """resolve `.` and `..` in path
    e.g 
        j.sals.fs.resolve("")  -> PosixPath('/home/rafy/Documents')
        j.sals.fs.resolve("./testing_text.txt")  -> PosixPath('/home/rafy/Documents/testing_text.txt')

    Args:
        path (str): path with optionally `.` and `..`

    Returns:
        str: resolved path
    """
    path=_str_to_path(path,needexist=True)
    return path.resolve()


def extension(path:Union[Path,str], include_dot=False):
    """Gets the extension of path
    e.g
        '/home/ahmed/myfile.py' -> `.py` if include_dot else `py`

    Args:
        path (str): [description]
        include_dot (bool, optional): controls whether to include the dot or not. Defaults to False.

    Returns:
        str: extension
    """
    path=_path_to_str(path,needexist=True)
    splitted = os.path.splitext(path)
    ext = ""
    if len(splitted) == 1:
        return ext

    if include_dot:
        return splitted[1]
    else:
        return splitted[1].strip(".")


ext = extension


def chown():
    raise err.NotImplemented("TODO:")


def read_link(path):
    raise err.NotImplemented("TODO:")


def remove_links(path):
    raise err.NotImplemented("TODO:")


def change_filenames(from_, to, where):
    raise err.NotImplemented("TODO:")


def replace_words_in_files(from_, to, where):
    raise err.NotImplemented("TODO:")


move = shutil.move


def default_filter_fun(entry):
    return True


def walk(path:Union[Path,str], pat="*", filter_fun=default_filter_fun):
    """walk recursively on path
    e.g
        for el in walk('/tmp', filter_fun=j.sals.fs.is_file) : ..
        for el in walk('/tmp', filter_fun=j.sals.fs.is_dir) : ..
        for el in walk('/tmp', filter_fun= lambda x: len(x)>4 and (j.sals.fs.is_file(x) or j.sals.fs.is_dir(x)) ) : ..


    Args:
        path (str): path to walk over
        pat (str, optional): pattern to match against. Defaults to "*".
        filter_fun (Function, optional): filtering function. Defaults to default_filter_fun which accepts anything.
    """
    path=_str_to_path(path,needexist=True)
    for entry in path.rglob(pat):
        # use rglob instead of glob("**/*")
        if filter_fun(entry):
            yield str(entry)


def walk_non_recursive(path:Union[Path,str], filter_fun=default_filter_fun):
    """walks non recursively on path
    e.g
        for el in walk('/tmp', filter=j.sals.fs.is_file) : ..
        for el in walk('/tmp', filter=j.sals.fs.is_dir) : ..
        for el in walk('/tmp', filter= lambda x: len(x)>4 and (j.sals.fs.is_file(x) or j.sals.fs.is_dir(x)) ) : ..


    Args:
        path (str): path to walk over
        pat (str, optional): pattern to match against. Defaults to "*".
        filter_fun (Function, optional): filtering function. Defaults to default_filter_fun which accepts anything.
    """
    path=_str_to_path(path,needexist=True)
    for entry in path.iterdir():
        if filter_fun(entry):
            yield str(entry)


def walk_files(path:Union[Path,str], recursive=True):
    """
    walk over files in path and applies function `fun`
    e.g

        for el in walk_files('/tmp') : ..

    Args:
        path (str): path to walk over
        recursive (bool, optional): recursive or not. Defaults to True.


    """
    path=_str_to_path(path,needexist=True)
    if recursive:
        return walk(path, filter_fun=is_file)
    else:
        return walk_non_recursive(path, filter_fun=is_file)


def walk_dirs(path, recursive=True):
    """
        walk over directories in path and applies function `fun`
    e.g

        for el in walk_dirs('/tmp') : ..


    Args:
        path (str): path to walk over
        recursive (bool, optional): recursive or not. Defaults to True.


    """
    path=_str_to_path(path,needexist=True)
    if recursive:
        return walk(path, filter_fun=is_dir)
    else:
        return walk_non_recursive(path, filter_fun=is_dir)




def fs_check(**arguments):
    """Abstracts common checks over your file system related functions.
    To reduce the boilerplate of expanding paths, checking for existence or ensuring non empty values.

    Checks are defined for each argument separately in a form of a set 
        e.g
        @fs_check(path={'required', 'exists', 'expand'})
        @fs_check(path1={'required', 'exists', 'expand'}, path2={'required', 'exists', 'expand'})    
        
    Available checks:
        - `required`: ensures the argument is passed with a non-empty value.
        - `expand`  : expands the tilde `~` in path.
        - `exists`  : the path exists.
        - `file`    : the path is a file.
        - `dir`     : the path is a dir.

    """


    for argument, validators in arguments.items():
        if not isinstance(validators, set):
            raise ValueError(f"Expected tuple of validators for argument {argument}")
        for validator in validators:
            if validator not in {"required", "exists", "file", "dir", "expand"}:
                raise ValueError(f"Unsupported validator '{validator}' for argument {argument}")

    def decorator(func):
        import inspect

        signature = inspect.signature(func)
        for argument in arguments:
            if signature.parameters.get(argument) is None:
                raise j.exceptions.Value(f"Argument {argument} not found in function declaration of {func.__name__}")

        def wrapper(*args, **kwargs):
            args = list(args)
            position = 0
            for parameter in signature.parameters.values():
                if parameter.name in arguments:
                    value = args[position] if position < len(args) else kwargs[parameter.name]
                    if isinstance(value, str):
                        value = expanduser(expandvars(value))
                    if position < len(args):
                        args[position] = value
                    else:
                        kwargs[parameter.name] = value

                    validators = arguments[parameter.name]
                    if value and validators.intersection({"exists", "file", "dir"}) and not exists(value):
                        msg = f"Argument {parameter.name} in {func.__name__} expects an existing path value! {value} does not exist."
                        raise j.exceptions.Value(msg)

                    if "required" in validators and (value is None or value.strip() == ""):
                        raise j.exceptions.Value(
                            f"Argument {parameter.name} in {func.__name__}  should not be None or empty string!"
                        )

                    if "required" in validators:
                        value = norm_path(value)
                        if position < len(args):
                            args[position] = value
                        else:
                            kwargs[parameter.name] = value

                    if value and validators.intersection({"file"}) and not isfile(value):
                        raise j.exceptions.Value(
                            f"Argument {parameter.name} in {func.__name__} expects a file path! {value} is not a file."
                        )
                    if value and validators.intersection({"dir"}) and not isdir(value):
                        raise j.exceptions.Value(
                            f"Argument {parameter.name} in {func.__name__} expects a directory path! {value} is not a directory."
                        )
                position += 1
            return fun(*args, **kwargs)

        return wrapper

    return decorator
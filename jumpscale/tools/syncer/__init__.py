from jumpscale.god import j
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
import gevent
from typing import List, Dict, Optional

DEFAULT_IGNORED_PATTERNS = [".git", ".pyc", "__pycache__", ".swp", ".swx"]


class Syncer(PatternMatchingEventHandler):
    def __init__(
        self,
        sshclients_names: List[str],
        paths: Dict[str, str],
        patterns: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None,
        ignore_directories: Optional[List[str]] = False,
        case_sensitive: bool = True,
    ):
        """Creates new syncer tool

        Arguments:
            sshclients_names {List[str]} -- list of sshclient names
            paths {Dict[str, str]} -- paths to watch src/dest form of dict {'/tmp/myproj':'/root/proj'}

        Keyword Arguments:
            patterns {Optional[List[str]]} -- optional list of patterns to watch (default: {None})
            ignore_patterns {Optional[List[str]]} -- patterns to ignore, e.g .git, __pycache__ (default: {None})
            ignore_directories {Optional[List[str]]} -- directories to ignore (default: {False})
            case_sensitive {bool} -- case sensitive watching  (default: {True})

        Returns:
            Syncer -- Syncer object
        """
        ignore_patterns = ignore_patterns or DEFAULT_IGNORED_PATTERNS
        super().__init__(patterns, ignore_patterns, ignore_directories, case_sensitive)
        self.observer = Observer()
        self.sshclients_names = sshclients_names
        self.paths = paths or {}  # src:dst

    def _get_dest_path(self, src_path: str) -> str:
        """returns destination path in remote machine

        Arguments:
            src_path {str} -- path in source machine

        Returns:
            str -- path in remote machine
        """
        j.logger.debug("paths: {} and path: {}".format(self.paths, src_path))

        for path in self.paths.keys():
            if path.startswith(src_path):
                return self.paths[src_path]

    def _rewrite_path_for_dest(self, src_path: str) -> str:
        """rewrite src_path to remote_path
        e.g
            local: /tmp/myproj/file.py
            remote: /root/myproj/file.py

        Arguments:
            src_path {str} -- source machine path

        Returns:
            str -- rewritten path for remote
        """
        # j.logger.debug("paths: {} and path: {}".format(self.paths, src_path))
        src_path = str(src_path)
        for path in self.paths.keys():
            if src_path.startswith(path):
                return src_path.replace(path, self.paths[path])

    def _get_sshclients(self):
        """Returns list of sshclient objects.

        Returns:
            List[SSHClient] -- list of ssh clients
        """
        clients = []
        for name in self.sshclients_names:
            clients.append(j.clients.sshclient.get(name))
        return clients

    def sync(self):
        """Sync directory structure and files

        """
        j.logger.debug("paths: {}".format(self.paths))

        def ensure_dirs():
            """For every directory in watched paths we make sure it's full path exists on remote.

            """
            for path in self.paths:
                for src_dir in j.sals.fs.walk_dirs(path):
                    dest_dir = str(self._rewrite_path_for_dest(src_dir))
                    for cl in self._get_sshclients():
                        cl.run("mkdir -p {}".format(dest_dir))

        def sync_file(e):
            """Sync single file to all registered sshclients

            Arguments:
                e {str} -- file path
            """
            dest_path = self._rewrite_path_for_dest(e)
            j.logger.debug("syncing {} to machines into {}".format(e, dest_path))

            for cl in self._get_sshclients():
                cl.run("mkdir -p {}".format(j.sals.fs.parent(dest_path)))
                cl.sftp.put(e, self._rewrite_path_for_dest(e))

        def filter_ignored(e):
            return True

        ensure_dirs()

        for path in self.paths:
            for f in j.sals.fs.walk_files(path, sync_file):
                pass

    def start(self, sync=True):
        """Start syncing/watching paths to remote machines

        Keyword Arguments:
            sync {bool} -- sync dirs/files first (default: {True})
        """
        if sync:
            self.sync()

        for path in self.paths.keys():
            self.observer.schedule(self, path)

        self.observer.start()
        try:
            while True:
                gevent.sleep(0.1)
        except KeyboardInterrupt:
            self.observer.unschedule_all()
            self.observer.stop()
        self.observer.join()

    def on_moved(self, event):
        super().on_moved(event)

        # what = "directory" if event.is_directory else "file"
        # j.logger.info("Moved {}: from {} to {}".format(what, event.src_path, event.dest_path))
        dest_path = self._rewrite_path_for_dest(event.dest_path)
        # j.logger.debug("will move to {}".format(dest_path))
        # j.logger.debug("will delete original in {}".format(self._rewrite_path_for_dest(event.src_path)))
        for cl in self._get_sshclients():
            if j.sals.fs.is_file(dest_path):
                cl.sftp.mkdir(j.sals.fs.parent(dest_path), ignore_existing=True)
            else:
                cl.sftp.mkdir(dest_path, ignore_existing=True)

            cl.sftp.put(event.dest_path, dest_path)
            cl.run("rm {}".format(event.src_path))

    def on_created(self, event):
        super().on_created(event)
        # what = "directory" if event.is_directory else "file"
        # j.logger.debug("Created {}: {}".format(what, event.src_path))

        dest_path = self._rewrite_path_for_dest(event.src_path)
        # j.logger.debug("will create in {}".format(dest_path))
        for cl in self._get_sshclients():
            cl.sftp.mkdir(j.sals.fs.parent(dest_path), ignore_existing=True)

            cl.run("touch {}".format(dest_path))

    def on_deleted(self, event):
        super().on_deleted(event)

        # what = "directory" if event.is_directory else "file"
        # j.logger.debug("Deleted {}: {}".format(what, event.src_path))

        dest_path = self._rewrite_path_for_dest(event.src_path)
        # j.logger.debug("will delete in {}".format(dest_path))
        for cl in self._get_sshclients():
            cl.run("rm {}".format(dest_path))

    def on_modified(self, event):
        super().on_modified(event)
        # what = "directory" if event.is_directory else "file"
        # j.logger.indebugfo("Modified {}: {}".format(what, event.src_path))

        # dest_path = self._rewrite_path_for_dest(event.src_path)
        # j.logger.debug("will modify in {}".format(dest_path))

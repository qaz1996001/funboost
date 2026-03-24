#coding=utf-8
import os
import re
import sys
import time
from nb_log import LoggerMixin, LoggerLevelSetterMixin
import paramiko


class ParamikoFolderUploader(LoggerMixin, LoggerLevelSetterMixin):
    """
    Folder upload implemented with paramiko.
    """

    def __init__(self, host, port, user, password, local_dir: str, remote_dir: str,
                 path_pattern_exluded_tuple=('/.git/', '/.idea/', '/dist/', '/build/'),
                 file_suffix_tuple_exluded=('.pyc', '.log', '.gz'),
                 only_upload_within_the_last_modify_time=3650 * 24 * 60 * 60,
                 file_volume_limit=1000 * 1000, sftp_log_level=20, pkey_file_path=None):
        """

        :param host:
        :param port:
        :param user:
        :param password:
        :param local_dir:
        :param remote_dir:
        :param path_pattern_exluded_tuple: Files matching these regex patterns are excluded
        :param file_suffix_tuple_exluded: Files with these suffixes are excluded
        :param only_upload_within_the_last_modify_time: Only upload files modified within this many seconds
        :param file_volume_limit: Files larger than this size (in bytes) are not uploaded
        :param sftp_log_level: Log level
        :param pkey_file_path: Private key file path. If set, uses private key authentication.
        """
        self._host = host
        self._port = port
        self._user = user
        self._password = password

        self._local_dir = str(local_dir).replace('\\', '/')
        if not self._local_dir.endswith('/'):
            self._local_dir += '/'
        self._remote_dir = str(remote_dir).replace('\\', '/')
        if not self._remote_dir.endswith('/'):
            self._remote_dir += '/'
        self._path_pattern_exluded_tuple = path_pattern_exluded_tuple
        self._file_suffix_tuple_exluded = file_suffix_tuple_exluded
        self._only_upload_within_the_last_modify_time = only_upload_within_the_last_modify_time
        self._file_volume_limit = file_volume_limit

        t = paramiko.Transport((host, port))
        if pkey_file_path is not None and os.path.exists(pkey_file_path):
            pkey = paramiko.RSAKey.from_private_key_file(pkey_file_path)
            t.connect(username=user, pkey=pkey)
        else:
            t.connect(username=user, password=password)
        self.sftp = paramiko.SFTPClient.from_transport(t)

        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, port=port, username=user, password=password, compress=True)
        self.ssh = ssh

        self.set_log_level(sftp_log_level)

    def _judge_need_filter_a_file(self, filename: str):
        ext = filename.split('.')[-1]
        if '.' + ext in self._file_suffix_tuple_exluded:
            return True
        for path_pattern_exluded in self._path_pattern_exluded_tuple:
            # print(path_pattern_exluded,filename)
            if re.search(path_pattern_exluded, filename):
                return True
        file_st_mtime = os.stat(filename).st_mtime
        volume = os.path.getsize(filename)
        if time.time() - file_st_mtime > self._only_upload_within_the_last_modify_time:
            return True
        if volume > self._file_volume_limit:
            return True
        return False

    def _make_dir(self, dirc, final_dir):
        """
        sftp.mkdir cannot directly create deeply nested directories.
        :param dirc:
        :param final_dir:
        :return:
        """
        # print(dir,final_dir)
        try:
            self.sftp.mkdir(dirc)
            if dirc != final_dir:
                self._make_dir(final_dir, final_dir)
        except (FileNotFoundError,):
            parrent_dir = os.path.split(dirc)[0]
            self._make_dir(parrent_dir, final_dir)

    def upload(self):
        for parent, dirnames, filenames in os.walk(self._local_dir):
            for filename in filenames:
                file_full_name = os.path.join(parent, filename).replace('\\', '/')
                if not self._judge_need_filter_a_file(file_full_name):
                    remote_full_file_name = re.sub(f'^{self._local_dir}', self._remote_dir, file_full_name)
                    try:
                        self.logger.debug(f'Local: {file_full_name}   Remote: {remote_full_file_name}')
                        self.sftp.put(file_full_name, remote_full_file_name)
                    except (FileNotFoundError,) as e:
                        # self.logger.warning(remote_full_file_name)
                        self._make_dir(os.path.split(remote_full_file_name)[0], os.path.split(remote_full_file_name)[0])
                        self.sftp.put(file_full_name, remote_full_file_name)
                else:
                    if '/.git' not in file_full_name and '.pyc' not in file_full_name:
                        self.logger.debug(f'Skipping upload of this file based on filter rules: {file_full_name}')


if __name__ == '__main__':
    uploader = ParamikoFolderUploader('192.168.6.133', 22, 'ydf', '372148', sys.path[1], '/home/ydf/codes/dssf/')
    uploader.upload()

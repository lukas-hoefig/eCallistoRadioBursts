#!./usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script based on requests to up-/and download files from the uni-graz nextcloud


:authors: 	Lukas Höfig, Roland Maderbacher
:contact: 	lukas.hoefig@edu.uni-graz.at
:date:       27.09.2022
"""

import requests
import zipfile
import os
import shutil
import gzip

import const

url = 'https://cloud.uni-graz.at/'

token_handle = "6j8jCKGy369pror"
token_download = "iKwKK25HwCz5jja"
token_upload = "sBLCnTW8fJBtpLD"
token_security = "oobta-Lngif-m2pZ7-HLxip-FWEXc"

path_download = const.path_data


def unzip(folder: str):
    """
    unzip all files in folder (.gz)
    """
    for file in os.listdir(folder):
        if file.endswith(const.file_type_zip):
            name_zipped = folder + file
            name_unzipped = (folder + file).rstrip(".gz")
            with gzip.open(name_zipped, "rb") as zipped:
                with open(name_unzipped, "wb+") as pure:
                    shutil.copyfileobj(zipped, pure)
            os.remove(name_zipped)


def deleteOnCloud(file: str, handle_token, secure_token) -> None:
    """
    Delete files in the Cloud folder, specified by the handle token, needs login credentials

    :param file: file to be deleted
    :param handle_token: folder token to the Cloud with write access
    :param secure_token: login credentials
    """

    full_url = url + 'public.php/webdav/' + file
    result = requests.delete(full_url, auth=(handle_token, secure_token))
    if not result.ok:
        raise ("Deletion of file failed with error code: ", result)


def uploadToCloud(file: str, handle_token, secure_token):
    """
    Uploads a file to a Cloud folder, specified by the handle token, needs login credentials

    :param file: file to be uploaded
    :param handle_token: folder token to the Cloud with write access
    :param secure_token: login credentials
    """

    name = file.rsplit("/")[-1]
    with open(file) as file_io:
        content = file_io.read()
    full_url = url + 'public.php/webdav/' + name
    result = requests.put(full_url, auth=(handle_token, secure_token), data=content)
    if not result.ok:
        print("Upload of file failed with error code: ", result)


def downloadFromCloud(token, path=path_download, delete=False, token_login=None):
    """
    Downloads all files from a a cloud folder and deletes them when asked

    :param token: access token, needs to have write access to delete
    :param path: download path
    :param delete: deletes file in the cloud folder if True
    :param token_login: login credentials, only needed if deletion is called
    """

    local_file = path + 'tmp.zip'
    if not os.path.isdir(path):
        os.makedirs(path)
    with zipfile.ZipFile(local_file, 'w'):
        pass

    full_url = url + 's/' + token + '/download'
    data = requests.get(full_url)

    if data.ok:
        with open(local_file, 'wb') as file:
            file.write(data.content)

        with zipfile.ZipFile(local_file, 'a') as zf:
            names = zf.namelist()
            folder = names[0]
            zf.extractall(path=path)
            for file in os.listdir(path + folder):
                shutil.move(path + folder + file, path + file)
            os.removedirs(path + folder)
        os.remove(local_file)

        if delete and token_login:
            for name in names[1:]:
                deleteOnCloud(name.rsplit("/")[-1], token, token_login)

    else:
        print("Request failed: ", data.ok)


if __name__ == "__main__":
    files = ["../test1.txt", "../test2.txt", "../test3.txt"]
    for i in files:
        uploadToCloud(i, token_handle, token_security)

    downloadFromCloud(token_handle, delete=True, token_login=token_handle)

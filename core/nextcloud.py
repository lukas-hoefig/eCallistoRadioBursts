#!./usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script based on requests to up-/and download files from the uni-graz nextcloud


:authors: 	Lukas Höfig, Roland Maderbacher
:contact: 	lukas.hoefig@edu.uni-graz.at
:date:       27.09.2022
:update:     04.07.2023
             added createNextcloudFolder()
"""

import requests
import zipfile
import os
import shutil
import gzip

import config

url = 'https://cloud.uni-graz.at/'

token_handle = "7GDQa6dPFjRenDT"
token_download = "5KLo9pHAXAtLzwm"
token_upload = token_handle
token_security = "KwQ4Ks48nL"

path_download = config.path_data


def unzip(folder: str):
    """
    unzip all files in folder (.gz)
    """
    print("unzipping", folder)
    for file in os.listdir(folder):
        if file.endswith(config.file_type_zip):
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


def createNextcloudFolder(folder_name, handle=token_upload, secure=token_security):
    """
    creates a folder in the nextcloud directory
    :param folder_name:
    :param handle:
    :param secure:
    """
    full_url = url + 'public.php/webdav/' + folder_name
    response = requests.request("MKCOL", full_url, auth=(handle, secure))
    if response.status_code == 201:
        print(f"Folder '{folder_name}' created successfully.")
    else:
        print(f"Failed to create folder. Status code: {response.status_code}")


def uploadToCloud(file: str, folder_on_cloud=None, handle=token_upload, secure=token_security):
    """
    Uploads a file to a Cloud folder, specified by the handle token, needs login credentials

    :param folder_on_cloud: specify the folder on the cloud
    :param handle: folder token to the Cloud with write access
    :param secure: login credentials
    :param file: file to be uploaded
    """
    if folder_on_cloud is None:
        folder = ""
    else:
        folder = folder_on_cloud
    name = file.rsplit("/")[-1]
    with open(file) as file_io:
        content = file_io.read()
    full_url = url + 'public.php/webdav/' + os.path.join(folder + name)
    result = requests.put(full_url, auth=(handle, secure), data=content)
    if not result.ok:
        print("Upload of file failed with error code: ", result)


def downloadFromCloud(token, path=path_download, delete=False, token_login=None):
    """
    Downloads all files from a next cloud folder and deletes them when asked

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

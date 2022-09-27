'''
Test to upload Files from a local directory to nextcloud share with "password",
download via different readonly share, delete from share.
All done by using the pypi REQUESTS module
and the python modules zipfile and os
'''

import requests
import zipfile
import os
import shutil

url = 'https://cloud.uni-graz.at/'  #tested on uni-graz nextcloud by Roland Maderbacher
transfer_dir = 'TRANSFER'           #local directory, has to exist with files inside
handle_token = 'example7iyBLQ5BmcsQyc2'    #read/write share on cloud
secure_token = 'exampleHYQBATPmsN2022'     #password for read/write share on cloud
download_token = 'example8AAWaYAWZCBKwTR'  #share to same path on cloud but readonly


def delete_on_cloud(filename,handle_token,secure_token):
    full_url = url + 'public.php/webdav/' + filename
    result = requests.delete(full_url, auth = (handle_token, secure_token))
    print('delete result:', result) #Response of webserver while testing


def upload_to_cloud(filename,handle_token,secure_token):
    name = filename.rsplit("/")[-1]
    with open(filename) as file:
        content = file.read()
    full_url = url + 'public.php/webdav/' + name
    result = requests.put(full_url, auth = (handle_token, secure_token), data = content)
    print('upload result:', result) #Response of webserver while testing


# def download_from_cloud(download_token):
#     local_file_name = 'local-copy.zip'
#     local_file = zipfile.ZipFile(local_file_name, 'w')
#     local_file.close()
#     full_url = url + 's/' + download_token + '/download'
#     data = requests.get(full_url)
# 
#     if data.ok:
#         with zipfile.ZipFile(local_file_name, 'r') as file:
#             print(data.content)
#             file.write(data.content)
# 
#         with zipfile.ZipFile(local_file_name, 'r') as zip_ref:
#             zip_ref.extractall()
#     else:
#         print("url request failed, request status: ", data.ok)

def download_from_cloud(download_token):
    if not os.path.isdir("./eCallistoData/realtime"):
        os.mkdir("eCallistoData/realtime/")
    local_file = './eCallistoData/realtime/local-copy.zip'
    with zipfile.ZipFile(local_file, 'w'):
        pass
    full_url = url + 's/' + download_token + '/download'
    data = requests.get(full_url)

    if data.ok:
        with open(local_file, 'wb') as file:
            file.write(data.content)

        with zipfile.ZipFile(local_file, 'a') as zf:
            names = zf.namelist()
            folder = names[0]
            zf.extractall(path="./eCallistoData/realtime/")
            for file in os.listdir("./eCallistoData/realtime/" + folder):
                shutil.move("./eCallistoData/realtime/" + folder + file, "./eCallistoData/realtime/" + file)    
            os.removedirs("./eCallistoData/realtime/" + folder)
        os.remove(local_file)
    else:
        print("Request failed: ", data.ok)

token_1 = "6j8jCKGy369pror"
token_2 = "oobta-Lngif-m2pZ7-HLxip-FWEXc"

filenamen = ["../test1.txt", "../test2.txt", "../test3.txt"]
for i in filenamen:
    print(i)
    upload_to_cloud(i, token_1,token_2)

download_from_cloud(token_1)

filenamen = ["test1.txt", "test2.txt", "test3.txt"]
for i in filenamen:
    delete_on_cloud(i,token_1,token_2)
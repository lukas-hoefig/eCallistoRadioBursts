'''
Test to upload Files from a local directory to nextcloud share with "password",
download via different readonly share, delete from share.
All done by using the pypi REQUESTS module
and the python modules zipfile and os
'''

import requests
import zipfile
import os


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
    full_url = url + 'public.php/webdav/' + filename
    result = requests.put(full_url, auth = (handle_token, secure_token), data = filename)
    print('upload result:', result) #Response of webserver while testing


def download_from_cloud(download_token):
    local_file = 'local-copy.zip'
    full_url = url + 's/' + download_token + '/download'
    data = requests.get(full_url)

    with open(local_file, 'wb') as file:
        file.write(data.content)

    with zipfile.ZipFile(local_file, 'r') as zip_ref:
        zip_ref.extractall()

 
#Testcase: upload - download(and extract) - delete
filenamen = os.listdir(transfer_dir)

for i in filenamen:
    print(i)
    upload_to_cloud(i,handle_token,secure_token)

   
download_from_cloud(download_token)

for i in filenamen:
    print(i)
    delete_on_cloud(i,handle_token,secure_token)
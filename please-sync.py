#!/bin/python3

import requests
import json
import os
import subprocess
from pathlib import Path

try:
    token=os.environ['PLEASE_SYNC_TOKEN']
except:
    print("Error: Export PLEASE_SYNC_TOKEN with your Gist access token")
    exit()

try:
    gist_id=os.environ['PLEASE_GIST_ID']
except:
    print("Error: Export PLEASE_GIST_ID with your Gist ID")
    exit()

try:
    pgp_id=os.environ['PLEASE_RECIPIENT_ID']
except:
    print("Error: Export PLEASE_RECIPIENT_ID with your Gist ID")
    exit()

home = str(Path.home()) + "/"
filename="please-sync-data.json"
please_config_path=".config/please/config.json"

## Get gist
def getGist():
    headers = {'Authorization': f'token {token}'}
    r = requests.get('https://api.github.com/gists/' + gist_id, headers=headers) 
    # print(r.json())
    return r.json()

## Update gist
def updateGist( content ):
    # content=open(filename, 'r').read()
    headers = {'Authorization': f'token {token}'}
    r = requests.patch('https://api.github.com/gists/' + gist_id, data=json.dumps({'files':{filename:{"content":content}}}),headers=headers) 
    #print(r.json())

# Get local config information. Drop ms and ns from epoch value
m_time_local = int(str(os.path.getmtime(home + please_config_path)).split('.',1)[0])
#print(m_time_local)

# Get gist, in JSON
remoteGistData = getGist()
# Get the content, in encrypted state, and convert into json object
remoteGistContent = json.loads(remoteGistData['files']['please-sync-data.json']['content'])
#print(remoteGistContent)
# Get modified date
m_time_remote = int(remoteGistContent['modified'])
#print(m_time_remote)

if m_time_local == m_time_remote:
    print("Local and Remote list is same")
elif m_time_local > m_time_remote:
    print("Local list newer than Remote")
    # Encrypt local data into ascii armored PGP encryption
    r = subprocess.run(args=[ "gpg",
                          "--recipient",
                          pgp_id,
                          "--encrypt",
                          "--armor",
                          "--output",
                          "-",
                          home + please_config_path],
                  universal_newlines = True,
                  stdout = subprocess.PIPE )
    #print(r.stdout.replace("\n", "\\n"))
    # Build JSON object
    config_data = {}
    config_data['modified'] = m_time_local
    config_data['data'] = r.stdout.replace("\n", "\\n")
    json_config_data = json.dumps(config_data)
    #print(json_config_data)
    updateGist( json_config_data )
else:
    print("Remote list newer than Local")
    # Backup local copy
    r = subprocess.run(args=["cp", "-r", home + please_config_path, home + please_config_path + ".bak"])
    # Get remote content
    remote_config_data = str(remoteGistContent['data']).replace("\\n","\n")
    #print(remote_config_data)
    # decrypt the data and overwrite local data
    echo_r = subprocess.Popen(('echo', remote_config_data), stdout=subprocess.PIPE)
    decrypt_r = subprocess.Popen(('gpg', '--decrypt'), stdin=echo_r.stdout, stdout=subprocess.PIPE)
    write_r = subprocess.Popen(('tee', home + please_config_path), stdin=decrypt_r.stdout, stdout=subprocess.PIPE)
    echo_r.wait()
    decrypt_r.wait()
    write_r.wait()
    print(decrypt_r.stdout)


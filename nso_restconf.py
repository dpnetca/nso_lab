#!/usr/bin/env python
"""
Interact with NSO using RESTCONF API's

For this script we will define a device to work with and complete
the following tasks as examples:
1> Check If device already exists delete it
2> create device
3> fetch SSH host keys from device
4> sync config from device
5> view some configuration (loopback interfaces)
6> create new loopback interface and view
7> update configuration (change loopback ip) and view
8> delete loopback interface and view

Author: Denis Pointer
"""

import requests
import json


class NsoRestConf:
    """
    Class for some basic NSO RESTCONF interaction
    """
    def __init__(self, username, password, hostname, port):
        """
        build base RESTCONF URL, authentication and header data
        """
        # TODO use .well-known to discover...
        self.base_url = f'http://{hostname}:{port}/restconf'
        self.auth = requests.auth.HTTPBasicAuth(username, password)
        self.headers = {"Content-Type": "application/yang-data+json"}

    def get_device_list(self):
        """
        Retrieve a list of device names from NSO

        Parameters:
          none

        Returns:
          LIST of device names
        """
        url = f"{self.base_url}/data/tailf-ncs:devices/device?depth=1"
        response = requests.get(url, auth=self.auth, headers=self.headers)
        device_list = [x['name'] for x in response.json()['tailf-ncs:device']]
        return device_list

    def delete_device(self, name):
        """
        Delete specified device from NSO

        Parameters:
          name: device name to be deleted

        Returns:
          request response
        """
        url = f"{self.base_url}/data/tailf-ncs:devices/device={name}"
        response = requests.delete(url, auth=self.auth, headers=self.headers)
        return response

    def create_device(self, name, address, port, authgroup, ned):
        """
        Create a New Device.

        Parameters:
          name: Unique device identifier name
          address: IP address of device
          port: Device ssh port
          authgroup: NSO authgroup to use
          ned: NSO NED to use for device

        Returns:
          request response
        """
        data = {
            "tailf-ncs:device": {
                "name": name,
                "address": address,
                "port": port,
                "authgroup": authgroup,
                "device-type": {
                    "cli": {
                        "ned-id": f'{ned}:{ned}'
                    }
                },
                "state": {
                    "admin-state": "unlocked"
                }
            }
        }
        data_json = json.dumps(data)
        url = f"{self.base_url}/data/tailf-ncs:devices"
        response = requests.post(url,
                                 data=data_json,
                                 auth=self.auth,
                                 headers=self.headers
                                 )
        return response

    def ssh_fetch_keys(self, name):
        """
        Kick off operation to retrieve SSH keys from device

        Parameters:
          name: device name
        Returns:
          request response
        """
        url = f"{self.base_url}/operations/devices/device={name}/ssh/"\
              "fetch-host-keys"
        response = requests.post(url, auth=self.auth, headers=self.headers)
        return response

    def sync_from(self, name):
        """
        Kick off operation to sync configuration from device to NSO

        Parameters:
          name: device name
        Returns:
          request response
        """
        url = f"{self.base_url}/operations/devices/device={name}/sync-from"
        response = requests.post(url, auth=self.auth, headers=self.headers)
        return response

    def get_device_loopbacks(self, name):
        """
        Retrieve a list of loopback interfaces, and associated config

        Parameters:
          name: device name
        Returns:
          LIST loopback DICT information
        """
        url = f"{self.base_url}/data/tailf-ncs:devices/device={name}/config/"\
            "tailf-ned-cisco-ios:interface/Loopback"
        response = requests.get(url, auth=self.auth, headers=self.headers)
        key = 'tailf-ned-cisco-ios:Loopback'
        loopback_list = [x for x in response.json()[key]]
        return loopback_list

    def create_device_loopbacks(self, device_name, loopback_name, ip, subnet):
        """
        Create a new loopback interface

        Parameters:
          device_name : device name
          loopback name: loopback name/number
          ip: ip address
          subnet: subnet mask
        Returns:
          request response
        """
        data = {
            "tailf-ned-cisco-ios:Loopback": {
                "name": loopback_name,
                "ip": {
                    "address": {
                        "primary": {
                            "address": ip,
                            "mask": subnet
                        }
                    }
                }
            }
        }
        data = json.dumps(data)
        url = f"{self.base_url}/data/tailf-ncs:devices/device={device_name}/"\
            "config/tailf-ned-cisco-ios:interface"
        response = requests.post(url,
                                 data=data,
                                 auth=self.auth,
                                 headers=self.headers
                                 )
        return response

    def update_device_loopback_ip(self, device_name, loopback_name, ip):
        """
        Change IP address of loopback interface

        Parameters:
          device_name : device name
          loopback name: loopback name/number
          ip: ip address
        Returns:
          request response
        """
        data = {"tailf-ned-cisco-ios:address": ip}
        data = json.dumps(data)
        url = f"{self.base_url}/data/tailf-ncs:devices/device={device_name}"\
            f"/config/tailf-ned-cisco-ios:interface/Loopback={loopback_name}"\
            "/ip/address/primary/address"
        response = requests.patch(url,
                                  data=data,
                                  auth=self.auth,
                                  headers=self.headers
                                  )
        return response

    def delete_device_loopback(self, device_name, loopback_name):
        """
        Delete a single loopback interface

        Parameters:
          device_name : device name
          loopback name: loopback name/number
        Returns:
          request response
        """
        url = f"{self.base_url}/data/tailf-ncs:devices/device={device_name}"\
            f"/config/tailf-ned-cisco-ios:interface/Loopback={loopback_name}"
        response = requests.delete(url, auth=self.auth, headers=self.headers)
        return response


def main():
    # DEFINE PARAMETERS TO USE FOR NEW DEVICE
    new_device = {
        'name': 'ios1',
        'address': '127.0.0.1',
        'port': '10023',
        'authgroup': 'netsim_auth',
        'ned': 'cisco-ios-cli-3.8'
    }
    # DEFINE PARAMETERS TO USE FOR NEW LOOPBACK INTERFACE
    new_loopback = {
        'device_name': 'ios1',
        'loopback_name': '50',
        'ip': '10.11.50.1',
        'subnet': '255.255.255.255'
    }

    # create NSO instance
    """
    NOTE typically credentials should not be stored in code shared or
    stored on GitHub, but as this is a lab it's the quick and easy
    way.  don't do this in a production environment
    """
    nso = NsoRestConf('admin', 'admin', '127.0.0.1', '8080')

    # retrieve and print a current list of devices in NSO
    device_list = nso.get_device_list()
    print(f'Initial Device List: {device_list}')

    # If our new device is already configured, delete it and update device list
    if new_device['name'] in device_list:
        print(f'\nDevice {new_device["name"]} already exists,'
              ' deleting device ... ', end='')
        response = nso.delete_device(new_device["name"])
        print(f'response: {response.status_code}')
        device_list = nso.get_device_list()
        print(f'updated Device List: {device_list}')

    # Create new device and print updated device list
    print(f'\nCreating new Device {new_device["name"]} ... ', end='')
    response = nso.create_device(**new_device)
    print(f'response: {response.status_code}')
    print(f'updated Device List: {nso.get_device_list()}')

    # Trigger NSO to getch SSH host keys from device
    print("\nFetching SSH HostKey ... ", end='')
    response = nso.ssh_fetch_keys(new_device["name"])
    print(f'response: {response.status_code} ...', end='')
    # success or fail returns 200 ok status code, check actual result
    print(f'result: {response.json()["tailf-ncs:output"]["result"]}')

    # Trigger NSO to syncronize configuration from the end device
    print("\nSync From Device ... ", end='')
    response = nso.sync_from(new_device["name"])
    print(f'response: {response.status_code} ...', end='')
    # success or fail returns 200 ok status code, check actual result
    print(f' result: {response.json()["tailf-ncs:output"]["result"]}')

    # retrieve and print a list of loopback interfaces
    print("\nRetrieving Device Loopbacks ... ")
    response = nso.get_device_loopbacks(new_device["name"])
    print(response)

    # create new loopback interface
    print("\nCreatint new loopback ... ", end='')
    response = nso.create_device_loopbacks(**new_loopback)
    print(f'response: {response.status_code}')

    # retrieve and print a list of loopback interfaces
    print("\nRetrieving Device Loopbacks ... ")
    response = nso.get_device_loopbacks(new_device["name"])
    print(response)

    # update the ip address on our new loopback interface
    print("\nUpdate Loopback IP ... ", end='')
    response = nso.update_device_loopback_ip('ios1', '50', '10.11.50.2')
    print(f'response: {response.status_code}')

    # retrieve and print a list of loopback interfaces
    print("\nRetrieving Device Loopbacks ... ")
    response = nso.get_device_loopbacks(new_device["name"])
    print(response)

    # delete the new loopback interface
    print("\nDelete Loopback ... ", end='')
    response = nso.delete_device_loopback('ios1', '50')
    print(f'response: {response.status_code}')

    # retrieve and print a list of loopback interfaces
    print("\nRetrieving Device Loopbacks ... ")
    response = nso.get_device_loopbacks(new_device["name"])
    print(response)


if __name__ == "__main__":
    main()

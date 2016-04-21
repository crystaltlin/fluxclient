
from fluxclient.utils.version import StrictVersion
from fluxclient.upnp.discover import UpnpDiscover
from .abstract_backend import NotSupportError
from .udp1_backend import UpnpUdp1Backend
from .ssl1_backend import UpnpSSL1Backend

BACKENDS = [
    UpnpSSL1Backend,
    UpnpUdp1Backend]


class UpnpTask(object):
    """UpnpTask provide basic configuration method to device

    :param uuid.UUID uuid: Device uuid, set UUID(int=0) while trying connect \
via ip address.
    :param encrypt.KeyObject client_key: Client key to connect to device.
    :param str ipaddr: IP Address to connect to.
    :param dict device_metadata: Device metadata
    :param dict backend_options: More configuration for UpnpTask
    :param callable lookup_callback: Invoke repeated while finding device
    :param float lookup_timeout: Raise error if device can not be found after \
timeout value
"""
    name = None
    uuid = None
    serial = None
    model_id = None
    version = None
    ipaddr = None
    meta = None

    _backend = None

    def __init__(self, uuid, client_key, ipaddr=None, device_metadata=None,
                 remote_profile=None, backend_options={}, lookup_callback=None,
                 lookup_timeout=float("INF")):
        self.uuid = uuid
        self.ipaddr = ipaddr
        self.client_key = client_key
        self.backend_options = backend_options

        if device_metadata:
            self.update_remote_profile(**device_metadata)
        elif remote_profile:
            self.update_remote_profile(**remote_profile)
        else:
            self.reload_remote_profile(lookup_callback, lookup_timeout)

        self.initialize_backend()

    def reload_remote_profile(self, lookup_callback=None,
                              lookup_timeout=float("INF")):
        def on_discovered(instance, **kw):
            self.update_remote_profile(**kw)
            instance.stop()

        if self.uuid.int:
            d = UpnpDiscover(uuid=self.uuid)
        else:
            d = UpnpDiscover(device_ipaddr=self.ipaddr)

        d.discover(on_discovered, lookup_callback, lookup_timeout)

    def update_remote_profile(self, uuid, name, serial, model_id, version,
                              ipaddr, **meta):
        if not self.uuid or self.uuid.int == 0:
            self.uuid = uuid
        self.name = name
        self.serial = serial
        self.model_id = model_id
        self.version = StrictVersion(version)
        self.ipaddr = ipaddr
        self.device_meta = meta

    def initialize_backend(self):
        for klass in BACKENDS:
            if klass.support_device(self.model_id, self.version):
                self._backend = klass(self.client_key, self.uuid, self.version,
                                      self.model_id, self.ipaddr,
                                      self.device_meta, self.backend_options)
                return

        raise NotSupportError(self.model_id, self.version)

    def add_trust(self):
        """Add client_key to device trust list"""
        self._backend.add_trust()

    def rename(self, new_name):
        """Rename device

        :param str new_name: New device name"""
        self._backend.rename(new_name)

    def modify_password(self, old_password, new_password, reset_acl=True):
        """Change device password, if **reset_acl** set to True, all other \
authorized user will be deauthorized.

        :param str old_password: Old device password
        :param str new_password: New device password
        :param bool reset_acl: Clear authorized user list in device"""
        self._backend.modify_password(old_password, new_password, reset_acl)

    def modify_network(self, **settings):
        """Mofify device modify_network, look document for more help"""

        self._backend.modify_network(**settings)

    def get_wifi_list(self):
        """Get wifi list discovered from device"""

        return self._backend.get_wifi_list()

import json

from ops.framework import Object, StoredState, EventsBase, EventBase, EventSource


class PrimaryChanged(EventBase):
    pass


class VRRPParametersRequiresEvents(EventsBase):
    primary_changed = EventSource(PrimaryChanged)


class VRRPInstance:

    def __init__(self, name, virtual_router_id, virtual_ip_addresses, network_interface,
                 track_interfaces=[], track_scripts=[]):
        self.name = name
        self.virtual_router_id = virtual_router_id
        self.virtual_ip_addresses = virtual_ip_addresses
        self.network_interface = network_interface
        self.track_interfaces = track_interfaces
        self.track_scripts = track_scripts


class VRRPScript:

    def __init__(self, name, path, timeout=1, interval=1, weight=0,
                 rise=1, fall=1, user='root', group='root'):
        self.name = name
        self.path = path
        self.timeout = timeout
        self.interval = interval
        self.weight = weight
        self.rise = rise
        self.fall = fall
        self.user = user
        self.group = group


class VRRPParametersRequires(Object):

    on = VRRPParametersRequiresEvents()
    state = StoredState()

    def __init__(self, charm, relation_name):
        super().__init__(charm, relation_name)
        self._relation_name = relation_name
        # TODO: should it support handling multiple primaries?
        self._relation = self.model.get_relation(relation_name)
        self.framework.observe(charm.on[relation_name].relation_changed, self.on_relation_changed)

    @property
    def vrrp_instances(self):
        if self._relation.units:
            primary_unit = self._relation.units[0]
            vrrp_instances_serialized = self._relation.data[primary_unit].get('vrrp_instances')
            vrrp_instances = []
            if vrrp_instances_serialized is not None:
                vrrp_instances = json.loads(vrrp_instances)
            return vrrp_instances

    def on_relation_changed(self, event):
        primary_unit = event.relation.units[0]
        if event.relation.data[primary_unit].get('vrrp_instances'):
            self.on.primary_changed.emit()


class KeepalivedAvailable(EventBase):
    pass


class VRRPParametersProvidesEvents(EventsBase):
    keepalived_available = EventSource(KeepalivedAvailable)


class VRRPParametersProvides(Object):

    on = VRRPParametersProvidesEvents()
    state = StoredState()

    def __init__(self, charm, relation_name):
        super().__init__(charm, relation_name)
        self._relation_name = relation_name
        self._relation = self.model.get_relation(relation_name)

        self.framework.observe(charm.on[relation_name].relation_joined, self.on_relation_joined)

    def configure_vrrp_instances(self, vrrp_instances):
        unit_data = self._relation.data[self.model.unit]
        unit_data['vrrp_instances'] = json.dumps(vrrp_instances, default=lambda obj: obj.__dict__)

    def on_relation_joined(self, event):
        self.on.keepalived_available.emit()

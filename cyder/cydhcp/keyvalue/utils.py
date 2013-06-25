from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist

from cyder.base.constants import IP_TYPE_4, IP_TYPE_6

from ipaddr import IPv4Address, IPv6Address, AddressValueError
import functools
import re


is_attr = re.compile("^attr_\d+$")


def list_validator(things, validator):
    return all([validator(thing.strip()) for thing in things.split(',')])


def is_valid_ip(ip, ip_type=None):
    def validate_ip(ip, addr_type):
        try:
            addr_type(ip)
            return True
        except AddressValueError:
            return False

    if ip_type == IP_TYPE_4:
        return validate_ip(ip, IPv4Address)
    elif ip_type == IP_TYPE_6:
        return validate_ip(ip, IPv6Address)
    else:
        return validate_ip(ip, IPv4Address) or validate_ip(ip, IPv6Address)


def is_valid_domain(name):
    if len(name) == 0:
        return False
    if name[-1] == '.':
        name = name[:-1]
    return all([re.match(r'^[_a-zA-Z\d]([_a-zA-Z0-9-]{0,61}[_a-zA-Z0-9])?$',
                         label) for label in name.split('.')]) \
           and len(name) <= 253


def is_valid_ip_or_domain(x, ip_type=None):
    return is_valid_ip(x, ip_type) or is_valid_domain(x)


def check_int(val, bits):
    return val.isdigit() and int(val) < (2 ** bits - 1)


def is_int8(val):
    return check_int(val, 8)


def is_int16(val):
    return check_int(val, 16)


def is_int32(val):
    return check_int(val, 32)


def is_bool(val):
    return val.lower() in ['on', 'off', 'true', 'false']


def is_ip_list(option_list, ip_type=None):
    return list_validator(option_list, lambda ip: is_valid_ip(ip, ip_type))


def is_ip_or_domain_list(option_list, ip_type=None):
    return list_validator(option_list,
                          lambda x: is_valid_ip_or_domain(x, ip_type))


def is_bool_and_ip_list(option_list, ip_type=None):
    # FIXME: if option_list was stripped before being stored, strip() on the
    # next line is not necessary
    option_list_parts = option_list.strip().split()
    if is_bool(option_list_parts[0]) and len(option_list_parts) == 2:
        return is_ip_list(option_list_parts[1], ip_type)
    else:
        return is_ip_list(option_list, ip_type)

def is_domain_list(option_list, ip_type=IP_TYPE_4):
    return list_validator(option_list, is_valid_domain)


def is_int32_list(val):
    return list_validator(val, is_int32)


def get_dhcp_aa(obj):
    members = dir(obj)
    aa = []
    for member in members:
        if member.startswith("_aa"):
            member_name = member[4:].replace('_', '-')
            aa.append(member_name)
    return aa


def get_aa(obj):
    members = dir(obj)
    aa = []
    for member in members:
        if member.startswith("_aa"):
            aa.append(member[4:])
    return aa


def get_attrs(query_dict):
    kv = {}
    for param, values in query_dict.iteritems():
        if (is_attr.match(param) and
                "{0}_value".format(param) in query_dict):
                # u'attr_0': [u'<attr>']
                # u'key_attr_0': [u'<attr_value>']
                key = query_dict[param]
                value = query_dict["{0}_value".format(param)]

                if key in kv:
                    raise ValidationError("{0} is already an "
                                          "attribute.".format(key))
                kv[key] = value

    return kv


def update_attrs(kv, attrs, KVClass, obj, obj_name):
    """
    :param kv: The KV pairs being added to the object.
    :type kv: dict
    :param attrs: The existing KV pairs.
    :type attrs: :class:`QuerySet`
    :param KVClass: The KeyValue Class being used to validate new KV pairs.
    :type KVClass: class
    :param obj: The object the KV paris are being associated to.
    :type obj: object
    :param obj_name: The name of the foreign key back to obj
    :type obj_name: str
    """
    to_save = []
    for attr, value in kv.iteritems():
        if not attr and not value:
            continue
        if attrs.filter(key=attr):
            kv = attrs.get(key=attr)
            kv.value = value
            to_save.append(kv)
        else:
            # This kv is new. Let's create it and add it to the
            # to_save list for saving!
            kv = KVClass(key=attr, value=value)
            to_save.append(kv)

    for kv in to_save:
        setattr(kv, obj_name, obj)
        kv.clean()
        kv.save()


def dict_to_kv(kv, KVClass):
    # All attrs wraps the new and old kv pairs in a KVClass to ensure
    # that the template knows how to render them.
    all_attrs = []
    for k, v in kv.iteritems():
        all_attrs.append(KVClass(key=k, value=v))
    return all_attrs


def get_dhcp_docstrings(obj):
    members = dir(obj)
    docs = []
    for member in members:
        if member.startswith("_aa"):
            if obj.is_option or obj.is_statement:
                member_name = member[4:].replace('_', '-')
            else:
                member_name = member[4:]
            docs.append((member_name, getattr(obj, member).__doc__))
    return docs


def get_docstrings(obj):
    members = dir(obj)
    docs = []
    for member in members:
        if member.startswith("_aa"):
            member_name = member[4:]
            docs.append((member_name, getattr(obj, member).__doc__))
    return docs


class AuxAttr(object):
    """
    This class is a quick hack and is quite magical. This class abstracts the
    retreval and creation of Key Value pairs. Example usage:

        >>> aa = AuxAttr(StaticIntrKeyValue, intr, 'intr')

    This initializes an :class:`AuxAttr` instance with StaticIntrKeyValue,
    (a class that inheirits from :class:`KeyValue`), an object that has
    a KeyValue store (in this case the 'intr' object of type
    :class:`StaticInterface`), and the :class:`str` 'intr' (the name of the
    object in the 'StaticIntrKeyValue' class).

    See the StaticInterface class for example usage for this class. Also see
    the unit tests.
    """

    def __init__(self, KeyValueClass, obj, obj_name):
        # Bypass our overrides.
        super(AuxAttr, self).__setattr__('obj', obj)
        super(AuxAttr, self).__setattr__('obj_name', obj_name)
        super(AuxAttr, self).__setattr__('KVClass', KeyValueClass)
        super(AuxAttr, self).__setattr__('cache', {})

    def _get_aa(self, attr):
        if attr in self.cache:
            return self.cache[attr]
        else:
            try:
                kv = self.KVClass.objects.get(**{'key': attr, self.obj_name:
                                                 self.obj})
            except ObjectDoesNotExist:
                raise AttributeError("{0} AuxAttr has no attribute "
                                     "{1}".format(self.KVClass, attr))
            self.cache[attr] = kv.value
            return kv.value
        raise AttributeError()

    def __getattr__(self, attr):
        raise AttributeError()

    def __getattribute__(self, attr):
        try:
            return super(AuxAttr, self).__getattribute__(attr)
        except AttributeError:
            pass
        return self._get_aa(attr)

    def __setattr__(self, attr, value):

        try:
            if super(AuxAttr, self).__getattribute__(attr):
                return super(AuxAttr, self).__setattr__(attr, value)
        except AttributeError:
            pass
        try:
            kv = self.KVClass.objects.get(**{'key': attr, self.obj_name:
                                             self.obj})
        except ObjectDoesNotExist:
            kv = self.KVClass(**{'key': attr, self.obj_name: self.obj})
        kv.value = value
        kv.clean()
        kv.save()
        self.cache[attr] = value
        return

    def __delattr__(self, attr):
        try:
            if super(AuxAttr, self).__getattribute__(attr):
                return super(AuxAttr, self).__delattr__(attr)
        except AttributeError:
            pass
        if hasattr(self, attr):
            self.cache.pop(attr)
            kv = self.KVClass.objects.get(**{'key': attr, self.obj_name:
                                             self.obj})
            kv.delete()
            return
        else:
            raise AttributeError("{0} AuxAttr has no attribute "
                                 "{1}".format(self.KVClass, attr))

import abc

import attr
import pytest

from labgrid import Target, target_factory
from labgrid.binding import BindingError
from labgrid.resource import Resource
from labgrid.driver import Driver
from labgrid.exceptions import NoSupplierFoundError, NoDriverFoundError, NoResourceFoundError


# test basic construction
def test_instanziation():
    t = Target("name")
    assert (isinstance(t, Target))


def test_get_resource(target):
    class A(Resource):
        pass

    a = A(target, "aresource")
    assert isinstance(target.get_resource(A), A)
    assert target.get_resource(A) is a
    assert target.get_resource(A, name="aresource") is a


def test_get_driver(target):
    class A(Driver):
        pass

    a = A(target, "adriver")
    assert isinstance(target.get_driver(A), A)
    assert target.get_driver(A) is a
    assert target.get_driver(A, name="adriver") is a


def test_getitem(target):
    class AProtocol(abc.ABC):
        pass

    class A(Driver, AProtocol):
        pass

    class B(Driver):
        pass

    a = A(target, "adriver")
    target.activate(a)
    assert isinstance(target[A], A)
    assert target[A] is a
    assert target[AProtocol] is a
    assert target[A, "adriver"] is a
    assert target[AProtocol, "adriver"] is a
    with pytest.raises(NoDriverFoundError) as excinfo:
        target[A, "bdriver"]
    assert "have other names" in excinfo.value.msg
    with pytest.raises(NoDriverFoundError) as excinfo:
        target[B, "adriver"]
    assert "no active driver" in excinfo.value.msg

    a2 = A(target, None)
    target.activate(a2)
    with pytest.raises(NoDriverFoundError) as excinfo:
        target[A]
    assert "multiple active drivers" in excinfo.value.msg


def test_no_resource(target):
    with pytest.raises(NoResourceFoundError):
        target.get_resource(Target)


def test_no_driver(target):
    with pytest.raises(NoDriverFoundError):
        target.get_driver(Target)


# test alternative suppliers
class ResourceA(Resource):
    pass


class ResourceB(Resource):
    pass


class DriverWithA(Driver):
    bindings = {"res": ResourceA}


class DriverWithASet(Driver):
    bindings = {"res": {ResourceA}, }


class DriverWithAB(Driver):
    bindings = {"res": {ResourceA, ResourceB}, }


def test_suppliers_a(target):
    ra = ResourceA(target, "resource")
    d = DriverWithA(target, "resource")
    assert d.res is ra


def test_suppliers_aset(target):
    ra = ResourceA(target, "resource")
    d = DriverWithASet(target, "driver")
    assert d.res is ra


def test_suppliers_ab_a(target):
    ra = ResourceA(target, "resource")
    d = DriverWithAB(target, "driver")
    assert d.res is ra


def test_suppliers_ab_b(target):
    rb = ResourceB(target, "resource")
    d = DriverWithAB(target, "driver")
    assert d.res is rb


def test_suppliers_ab_both(target):
    ra = ResourceA(target, "resource_a")
    rb = ResourceB(target, "resource_b")
    with pytest.raises(NoSupplierFoundError):
        d = DriverWithAB(target, "driver")


def test_suppliers_ab_missing(target):
    with pytest.raises(NoSupplierFoundError):
        d = DriverWithAB(target, "driver")


class DriverWithNamedA(Driver):
    bindings = {
        "res": Driver.NamedBinding(ResourceA),
    }


def test_suppliers_named_a(target):
    ra = ResourceA(target, "resource")
    target.set_binding_map({"res": "resource"})
    d = DriverWithNamedA(target, "driver")
    assert d.res is ra


class DriverWithMultiA(Driver):
    bindings = {
        "res1": ResourceA,
        "res2": ResourceA,
    }


def test_suppliers_multi_a(target):
    ra1 = ResourceA(target, "resource1")
    with pytest.raises(BindingError) as excinfo:
        DriverWithMultiA(target, "driver")
    assert "duplicate bindings" in excinfo.value.msg


def test_suppliers_multi_a_explict(target):
    ra1 = ResourceA(target, "resource1")
    ra2 = ResourceA(target, "resource2")
    target.set_binding_map({
        "res1": "resource1",
        "res2": "resource2",
    })
    d = DriverWithMultiA(target, "driver")
    assert d.res1 is ra1
    assert d.res2 is ra2


class DriverWithNamedMultiA(Driver):
    bindings = {
        "res1": Driver.NamedBinding(ResourceA),
        "res2": Driver.NamedBinding(ResourceA),
    }


def test_suppliers_multi_named_a(target):
    ra1 = ResourceA(target, "resource1")
    ra2 = ResourceA(target, "resource2")
    target.set_binding_map({
        "res1": "resource1",
        "res2": "resource2",
    })
    d = DriverWithNamedMultiA(target, "driver")
    assert d.res1 is ra1
    assert d.res2 is ra2


# test nested resource creation
@attr.s(cmp=False)
class DiscoveryResource(Resource):
    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        ResourceA(self.target, "resource")

def test_nested(target):
    rd = DiscoveryResource(target, "discovery")
    d = DriverWithAB(target, "driver")
    assert isinstance(d.res, ResourceA)

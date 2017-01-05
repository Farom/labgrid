import attr

from ..binding import BindingError, BindingMixin


@attr.s
class Driver(BindingMixin):
    """
    Represents a driver which is used externally or by other drivers. It
    implements functionality based on directly accessing the Resource or by
    building on top of other Drivers.

    Life cycle:
    - create
    - bind (n times)
    - activate
    - usage
    - deactivate
    """

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        if self.target is None:
            raise BindingError("Drivers can only be created on a valid target")

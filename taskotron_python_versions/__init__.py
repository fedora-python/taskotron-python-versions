from .executables import task_executables
from .naming_scheme import task_naming_scheme
from .requires import task_requires_naming_scheme
from .two_three import task_two_three
from .unversioned_shebangs import task_unversioned_shebangs


__all__ = (
    'task_two_three',
    'task_naming_scheme',
    'task_requires_naming_scheme',
    'task_executables',
    'task_unversioned_shebangs',
)

## Version 4.3.0

* Add validate UTC timezone for datetime fields in `BaseSchema`.
* Remove Python version 3.9 and 3.10.

## Version 4.2.0

* Add method `.to_dict()` to `ModelMixin`.
* Add validate UTC timezone for datetime field in `ModelMixine`.

## Version 4.1.0

* Add bulk methods to `CreateMixin`, `ReadMixin`, `UpdateMixin` and `DeleteMixin` mixins.

## Version 4.0.0

* Add `Validation` decorators.

## Version 3.0.0

* Add method `paginate()` to `ReadMixin`.
* Change interface for methods `read()` from `ReadMixin`, `delete()` from `DeleteMixin`.

## Version 2.1.0

* `PaginateMixin` removed, this functional moved to `ReadMixin`.
* Add parameter `deserialize` to `CreateMixin`, `ReadMixin` and `UpdateMixin`.
* Improved docstrings.


## Version 2.0.0

* Refactoring of the module has been carried out. Improved class and method interfaces.

## Version 1.0.0

* Initial public release.

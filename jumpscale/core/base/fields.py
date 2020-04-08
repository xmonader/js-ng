"""
`fields` have all possible fields where they can be used as a class variables for any Base classselfself.

Field instances will not hold the value or any date, they will be converted by Base to function descriptors,
where the data itself resides in Base objects (instances).

See `jumpscale.core.base.meta`.

Example:

```python
from enum import Enum

class Permission(Base):
    read_posts = fields.Boolean()
    write_posts = fields.Boolean()
    open_ticket = fields.Boolean()


class UserType(Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    emails = fields.List(fields.String())
    permissions = fields.List(fields.Object(Permission))
    custom_config = fields.Typed(dict)
    type = fields.Enum(UserType)

user = User()
emails = ["a@b.com"]
perm1 = Permission()
perm1.open_portal = True
permissions = [perm1]

user.emails = emails
user.permissions = permissions
user.save()
```

Every field type is responsible dealing with the actual value of this field in the Base objects (instances), mainly:

* validation
* converting from raw primitive types to special types if any, which would help in serialization

In addition to custom options every field can accept and define, they can be used in the following methods:

* `validate`:  raises a `ValidationError` in case it's not valid.
* `to_raw`: returns a raw (primitive type) object from a value of this field
* `from_raw`: returns a new object of the field type (if any) from a raw value

No need for `from_raw` to raise an error on e.g. type mismatch, as `validate` will do the validation.

"""
import datetime
import enum
import ipaddress
import re
import time

from urllib.parse import urlparse

from .factory import StoredFactory


class ValidationError(Exception):
    """
    base type for any validation error
    """


class Field:
    def __init__(self, default=None, required=False, indexed=False, readonly=False, validators=None, **kwargs):
        """
        Base field for all field types, have some common options that can be used any other field type too.


        Args:
            default (any, optional): default value. Defaults to None.
            required (bool, optional): required or not. Defaults to False.
            indexed (bool, optional): indexed or not. Defaults to False.
            readonly (bool, optional): can only get the value. Defaults to False.
            validators (list of function, optional): a list of functions that takes a value and raises ValidationError if not valid. Defaults to None.
        """
        self.default = default
        self.required = required
        self.indexed = indexed
        self.readonly = readonly
        self.kwargs = kwargs

        self.validators = validators
        if self.validators is None:
            self.validators = []

        # self.validate = Schema({

        # })

    def validate(self, value):
        """
        validate value if required and call custom self.validators if any

        Args:
            value (any): in case value is not valid

        Raises:
            ValidationError: [description]
        """
        if value is None:
            if self.required:
                raise ValidationError("field is required")
        for validator in self.validators:
            validator(value)

    def from_raw(self, value):
        """
        get the value of this field from primitive raw types

        Args:
            value (any): support value by this field type (if any)

        Returns:
            any: raw value
        """
        return value

    def to_raw(self, value):
        """
        get the raw value of this field

        Args:
            value (any): current value of this field

        Returns:
            any: a primitive raw value
        """
        return value


class Typed(Field):
    def __init__(self, type_, **kwargs):
        """
        base field for any type, value mus tof of `type_`

        Args:
            type_ (type): any type (class)
            kwargs: any keyword arguments supported by `Field`
        """
        self.type = type_
        super().__init__(**kwargs)

    def validate(self, value):
        super().validate(value)
        if value is not None:
            if not isinstance(value, self.type):
                raise ValidationError(f"value is not of type {self.type}")


class Boolean(Typed):
    def __init__(self, default=False, **kwargs):
        """
        Boolean fields to hold a bool value

        Args:
            default (bool, optional): default value. Defaults to False.
            kwargs: any keyword arguments supported by `Field`
        """
        super().__init__(type_=bool, default=default, **kwargs)


class Integer(Typed):
    def __init__(self, default=0, min=None, **kwargs):
        """
        Intger field, the same as `Typed`, but with a type of `int`

        It can have a minimum value, if min is not set, it will ignore it.

        Args:
            default (int, optional): default value. Defaults to 0.
            min (int, optional): minimum value. Defaults to None.
            kwargs: any keyword arguments supported by `Field`
        """
        self.min = min
        super().__init__(type_=int, default=default, min=min, **kwargs)

    def validate(self, value):
        super().validate(value)
        if self.min is not None:
            if value < self.min:
                raise ValidationError(f"cannot set values less than {self.min}")


class Float(Typed):
    def __init__(self, default=0.0, **kwargs):
        """
        Same as `Integer` field, but with a type of `float`.

        Args:
            default (float, optional): default value. Defaults to 0.0.
            kwargs: any keyword arguments supported by `Field`
        """
        super().__init__(type_=float, default=default, min=min, **kwargs)


class String(Typed):
    def __init__(self, maxlen=None, **kwargs):
        """
        Same as `Typed`, but with a type of `str`.

        If maxlen is set, it will validate the length of the string.

        Args:
            maxlen (int): maximum length allowed. Defaults to None
            kwargs: any keyword arguments supported by `Field`
        """
        super().__init__(type_=str, **kwargs)
        self.maxlen = maxlen

    def validate(self, value):
        super().validate(value)
        if self.maxlen is not None:
            if len(value) > self.maxlen:
                raise ValidationError(f"length of the string exceeds {self.maxlen}")


class Secret(String):
    """
    Same as `String`, but encrypted by default.

    Should be used with sensitive data.

    Args:
        maxlen (int): maximum length allowed. Defaults to None
        kwargs: any keyword arguments supported by `String`
    """


class Object(Typed):
    def __init__(self, type_, type_kwargs=None, **kwargs):
        """
        An embedded Base object field of any type.

        Args:
            type_ (type): Base object type (class)
            type_kwargs (dict, optional): kwargs as a dict to be passed to Base instance when created. Defaults to None.
            kwargs: any keyword arguments supported by `Field`
        """
        super().__init__(type_=type_, **kwargs)
        self.type_kwargs = type_kwargs

        if self.type_kwargs is None:
            self.type_kwargs = {}

        if not self.default:
            self.default = self.type(**self.type_kwargs)

    def validate(self, value):
        """
        validate Base objects

        Args:
            value (Base): object
        """
        super().validate(value)
        try:
            value.validate()
        except AttributeError:
            raise ValidationError("object of Base must have validate()")

    def to_raw(self, obj):
        """
        get raw value of an object as dict

        Args:
            obj (Base): base object

        Returns:
            dict: raw data
        """
        return obj._get_data()

    def from_raw(self, data):
        """
        get an object from dict

        Args:
            data (dict): data dict

        Returns:
            Base: base object
        """
        if isinstance(data, dict):
            obj = self.type()
            obj._set_data(data)
            return obj
        return data


class List(Field):
    def __init__(self, field, **kwargs):
        """
        A list field for any field types.

        Args:
            field (Field): a field instance of any fields, e.g. `fields.String(maxlen=14)`.
            kwargs: any keyword arguments supported by `Field`
        """
        self.field = field
        super().__init__(**kwargs)

    def validate(self, value):
        """
        validate the value of every item in the list
        Will just call the field.validate of the given field
        """
        super().validate(value)

        if value is None:
            value = []

        for item in value:
            self.field.validate(item)

    def to_raw(self, values):
        """
        get a list of values as raw

        Args:
            values (list): list of items of field type

        Returns:
            list: list of raw values
        """
        if not values:
            return []

        return [self.field.to_raw(value) for value in values]

    def from_raw(self, values):
        """
        get a list of field type from raw values

        Args:
            values (list): list of raw values

        Returns:
            list: list of objects of field type
        """
        if not values:
            return []

        return [self.field.from_raw(value) for value in values]


class Enum(Typed):
    def __init__(self, enum_type, **kwargs):
        """
        enum field, to be used with `enum.Enum`.
        Example:

        ```python
        class UserType(Enum):
            USER = "user"
            ADMIN = "admin"
        ```

        field = fields.Enum(UserType)

        Args:
            enum_type (type): enum type (class)
            kwargs: any keyword arguments supported by `Field`
        """
        # default is the first value
        default = next(iter(enum_type))
        super().__init__(type_=enum_type, default=default, **kwargs)
        self.enum_type = enum_type

    def to_raw(self, enum_obj):
        """
        get enum value

        Args:
            enum_obj (enum.Enum): enum object

        Returns:
            any: enum value
        """
        return enum_obj.value

    def from_raw(self, value):
        """
        get an enum object from value

        Args:
            value (any): any value

        Returns:
            enum: enum object of enum type of the field
        """
        try:
            return self.enum_type(value)
        except ValueError:
            # let validate() do the validation
            return value


class Email(Field):
    def __init__(self, default="", **kwargs):
        """
        email field, will validate the value of emails

        Args:
            default (str, optional): default value. Defaults to ""
            kwargs: any keyword arguments supported by `Field`
        """
        super().__init__(default, **kwargs)
        self.regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    def validate(self, value):
        """
        check whether provided value is a valid email representation

        Args:
            value (str)

        Raises:
            ValidationError: in case the value is not a telephone
        """
        super().validate(value)
        if not re.match(self.regex, value):
            raise ValidationError(f"{value} is not a valid Email address")


class Path(Field):
    # TODO: Validate that it is working on windows
    def __init__(self, default="", **kwargs):
        """
        path field, will validate the value of file system paths

        Args:
            default (str, optional): default value. Defaults to ""
            kwargs: any keyword arguments supported by `Field`
        """
        super().__init__(default, **kwargs)
        self.regex = r"^(/[^/ ]*)+/?$"

    def validate(self, value):
        """
        check whether provided value is a valid path representation

        Args:
            value (str)

        Raises:
            ValidationError: in case the value is not a telephone
        """
        super().validate(value)
        if not re.match(self.regex, value):
            raise ValidationError(f"{value} is not a valid Path")


class URL(Field):
    def __init__(self, default="", **kwargs):
        """
        url field, will validate the value of urls

        Args:
            default (str, optional): default value. Defaults to ""
            kwargs: any keyword arguments supported by `Field`
        """
        super().__init__(default, **kwargs)
        self.regex = r"^(https?|ftp)://[^\s/$.?#].[^\s]*$"

    def validate(self, value):
        """
        check whether provided value is a valid URL representation

        Args:
            value (str)

        Raises:
            ValidationError: in case the value is not a telephone
        """
        super().validate(value)
        url = urlparse(value)
        if not url.scheme or not url.netloc:
            raise ValidationError(f"{value} is not a valid URL address")


class Tel(Field):
    def __init__(self, default="", **kwargs):
        """
        email field, will validate the value of telephone numbers

        will be stored as a string at the end.

        It will strip any additional characters that are not numbers.

        Args:
            default (str, optional): default value. Defaults to ""
            kwargs: any keyword arguments supported by `Field`
        """
        super().__init__(default, **kwargs)
        self.regex = r"^\+?[0-9]{6,15}(?:x[0-9]+)?$"

    def validate(self, value):
        """
        check whether provided value is a valid telephone number representation

        Args:
            value (str)

        Raises:
            ValidationError: in case the value is not a telephone
        """
        super().validate(value)
        if not re.search(self.regex, value):
            raise ValidationError(f"{value} is not a valid Telephone")

    def from_raw(self, value):
        """clean the telephone function from unwanted signs like , - ( )"""
        if value is not None:
            value = value.replace(",", "")
            value = value.replace("-", "")
            value = value.replace("(", "")
            value = value.replace(")", "")
            value = value.replace(" ", "")
            return value
        return value


class IPAddress(Field):
    def __init__(self, default="", **kwargs):
        """
        ip address field, will validate the value of ip address (v4 and v6)

        will be stored as a string.

        Args:
            default (str, optional): default value. Defaults to ""
            kwargs: any keyword arguments supported by `Field`
        """
        super().__init__(default, **kwargs)

    def validate(self, value):
        """
        check whether provided value is a valid IPaddress representation
        including IPv4,IPv6 and network

        Args:
            value (str)

        Raises:
            ValidationError: in case the value is not a telephone
        """

        super().validate(value)
        try:
            ipaddress.ip_interface(value)
        except Exception:
            raise ValidationError(f"{value} is not a valid IP address")


class DateTime(Typed):
    # maybe add something like auto_now and auto_today for date/time fields
    def __init__(self, default=None, format_=None, **kwargs):
        """
        datetime field, actual value will be converted to datetime (utc) object

        Args:
            default (datetime): default value. Defaults to None.
            format_ (str, optional): datetime format. Defaults to "%Y-%m-%d %H:%M" if None.
            kwargs: any keyword arguments supported by `Field`
        """
        super().__init__(type_=datetime.datetime, default=default, **kwargs)
        if not format_:
            format_ = "%Y-%m-%d %H:%M"
        self.format = format_

    def from_raw(self, value):
        """
        get a datetime object from a numberic (epoch) or string value


        Args:
            value (str or int or float): value as a number or a string

        Returns:
            datetime.datetime: `datetime.datetime` object
        """
        if isinstance(value, (int, float)):
            return datetime.datetime.utcfromtimestamp(value)
        elif isinstance(value, str):
            return datetime.datetime.strptime(value, self.format)
        return value

    def to_raw(self, dt_obj):
        """
        get a utc timestamp from datetime object

        Args:
            dt_obj (datetime.datetime): datetime object

        Returns:
            float: utc timestamp
        """
        if isinstance(dt_obj, datetime.date):
            return dt_obj.replace(tzinfo=datetime.timezone.utc).timestamp()
        return dt_obj


class Date(Typed):
    def __init__(self, default=None, format_=None, **kwargs):
        """
        date field, actual value will be converted to date object

        Args:
            default (date): default value. Defaults to None.
            format_ (str, optional): date format. Defaults to "%Y-%m-%d" if None.
            kwargs: any keyword arguments supported by `Field`
        """
        super().__init__(type_=datetime.date, default=default, **kwargs)
        if not format_:
            format_ = "%Y-%m-%d"
        self.format = format_

    def from_raw(self, value):
        """
        get a date object from a numberic (epoch) or string value


        Args:
            value (str or int or float): value as a number or a string

        Returns:
            datetime.date: `datetime.date` object
        """
        if isinstance(value, (int, float)):
            return datetime.date.fromtimestamp(value)
        elif isinstance(value, str):
            try:
                return datetime.datetime.strptime(value, self.format).date()
            except ValueError:
                pass
        return value

    def to_raw(self, d_obj):
        """
        get a utc timestamp from date object

        Args:
            d_obj (datetime.date): date object

        Returns:
            float: timestamp (epoch)
        """
        if isinstance(d_obj, datetime.date):
            return time.mktime(d_obj.timetuple())
        return d_obj


class Time(Typed):
    def __init__(self, default=None, format_=None, **kwargs):
        """
        time field, actual value will be converted to time object

        Args:
            default (date): default value. Defaults to None.
            format_ (str, optional): time format. Defaults to "%H:%M" if None.
            kwargs: any keyword arguments supported by `Field`
        """
        super().__init__(default=default, type_=datetime.time, **kwargs)
        if not format_:
            format_ = "%H:%M"
        self.format = format_
        self.mktime_format = "%a %b %d %H:%M:%S %Y"

    def from_raw(self, value):
        """
        get a time object from a numberic or string value


        Args:
            value (str or int or float): value as a number or a string

        Returns:
            datetime.time: `datetime.time` object
        """
        if isinstance(value, (int, float)):
            return datetime.datetime.utcfromtimestamp(value).time()
        elif isinstance(value, str):
            try:
                return datetime.datetime.strptime(value, self.format).time()
            except ValueError:
                pass
        return value

    def to_raw(self, t_obj):
        """
        get a utc timestamp from t_obj object

        Args:
            t_obj (datetime.time): time object

        Returns:
            float: timestamp (epoch)
        """
        if isinstance(t_obj, datetime.time):
            dt_obj = datetime.datetime(
                1970, 1, 1, t_obj.hour, t_obj.minute, t_obj.second, int(t_obj.microsecond / 1000)
            )
            return dt_obj.replace(tzinfo=datetime.timezone.utc).timestamp()
        return t_obj


# TODO: add duration field
class Factory(StoredFactory):
    pass

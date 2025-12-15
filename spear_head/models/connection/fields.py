"""

"""

from enum import Enum
from attr import dataclass
from spear_head.constants.constants import INT_FIELD_SIZE, SOCKET_FIELD_LENGTH_SIZE, SOCKET_FULL_LENGTH_SIZE

class FieldType(Enum):
    """
    Enumeration for different field types.
    """
    INT = 0
    RAW = 1
    TEXT = 2

    @staticmethod
    def from_byte(value: int) -> 'FieldType':
        """
        Convert a byte value to the corresponding FieldType.

        Args:
            value (int): The byte value representing the field type.

        Returns:
            FieldType: The corresponding FieldType enumeration member.

        Raises:
            ValueError: If the byte value does not correspond to any FieldType. Or invalid byte value.
        """
        if not isinstance(value, int) or not (0 <= value <= 255):
            raise ValueError(f"Value must be a byte (0-255), got: {value}")

        for field_type in FieldType:
            if field_type.value == value:
                return field_type
        
        return FieldType.RAW  # Default to RAW if unknown

    def to_byte(self) -> int:
        """
        Convert the FieldType to its corresponding byte value.

        Returns:
            int: The byte value representing the field type.
        """
        return self.value


@dataclass
class Field:
    """
    Represents a field with a specific type and value.
    """

    type_: FieldType
    value: bytearray

    def __init__(self, type_: FieldType, value: bytearray | int | bytes | str) -> None:
        self.type_ = type_
        if type_ == FieldType.INT:
            if not isinstance(value, int) and not isinstance(value, bytes) and not isinstance(value, bytearray):
                raise TypeError(f"INT field requires int, bytes, or bytearray, got: {type(value)}")

            if isinstance(value, bytes) or isinstance(value, bytearray):
                if len(value) != INT_FIELD_SIZE:
                    raise ValueError(f"INT field requires {INT_FIELD_SIZE} bytes, got: {len(value)} bytes")
                self.value = bytearray(value)
                return

            max_bits = INT_FIELD_SIZE * 8
            min_val = -(1 << (max_bits - 1))
            max_val = (1 << (max_bits - 1)) - 1

            if not (min_val <= value <= max_val):
                raise ValueError(
                    f"Integer {value} out of range for {INT_FIELD_SIZE}-byte signed integer"
                )

            self.value = bytearray(value.to_bytes(INT_FIELD_SIZE, byteorder="big", signed=True))
            return

        if type_ == FieldType.RAW:
            if isinstance(value, bytearray):
                self.value = value
                return

            if isinstance(value, bytes):
                self.value = bytearray(value)
                return

            raise TypeError(f"RAW field requires bytes or bytearray, got: {type(value)}")

        if type_ == FieldType.TEXT:
            if not isinstance(value, str) and not isinstance(value, bytes) and not isinstance(value, bytearray):
                raise TypeError(f"TEXT field requires str, bytes, or bytearray, got: {type(value)}")

            encoded = value.encode("utf-8") if isinstance(value, str) else value
            self.value = bytearray(encoded)
            return

        raise ValueError(f"Unhandled FieldType: {type_}")

    def to_bytes(self) -> bytearray:
        """
        Serialize the Field to bytes, including length, type and value.

        Returns:
            bytearray: The serialized byte representation of the Field.
        """
        result = bytearray()
        length = len(self.value) + 1 # +1 for the type byte
        result.extend(length.to_bytes(SOCKET_FIELD_LENGTH_SIZE, byteorder="big"))
        result.append(self.type_.to_byte())
        result.extend(self.value)
        return result

    def as_str(self) -> str:
        """
        Get the field value as a string.
        Returns:
            str: The string representation of the field value."""
        if self.type_ != FieldType.TEXT:
            raise TypeError("Field is not of type TEXT")
        return self.value.decode("utf-8", errors="replace")
    
    def as_int(self) -> int:
        """
        Get the field value as an integer.
        Returns:
            int: The integer representation of the field value.
        """
        if self.type_ != FieldType.INT:
            raise TypeError("Field is not of type INT")
        return int.from_bytes(self.value, byteorder="big", signed=True)
    
    def as_raw(self) -> bytes:
        """
        Get the field value as raw bytes.
        Returns:
            bytes: The raw byte representation of the field value.
        """
        if self.type_ != FieldType.RAW:
            raise TypeError("Field is not of type RAW")
        return bytes(self.value)

    def __str__(self) -> str:
        if self.type_ == FieldType.INT:
            int_value = int.from_bytes(self.value, byteorder="big", signed=True)
            return f"Field(INT: {int_value})"
        if self.type_ == FieldType.RAW:
            return f"Field(RAW: {self.value.hex()})"
        if self.type_ == FieldType.TEXT:
            text_value = self.value.decode("utf-8", errors="replace")
            return f"Field(TEXT: {text_value})"
        return f"Field(UNKNOWN TYPE {self.type_}: {self.value})"

class Fields:
    """
    Collection of Field instances.
    """

    fields: list[Field]
    seek_: int

    def __init__(self, fields: list[Field]) -> None:
        self.fields = fields
        self.seek_ = 0

    def to_bytes(self, include_length: bool = True) -> bytearray:
        """
        Serialize all Fields to bytes.

        Args:
            include_length (bool): Whether to include the total length prefix.

        Returns:
            bytearray: The serialized byte representation of all Fields.
        """
        result = bytearray()
        result.extend(b'\x00' * SOCKET_FULL_LENGTH_SIZE)  # Placeholder
        for field in self.fields:
            result.extend(field.to_bytes())

        if not include_length:
            return result[SOCKET_FULL_LENGTH_SIZE:]

        total_length = len(result) - SOCKET_FULL_LENGTH_SIZE
        result[0:SOCKET_FULL_LENGTH_SIZE] = total_length.to_bytes(SOCKET_FULL_LENGTH_SIZE, byteorder="big")

        return result
    
    @staticmethod
    def from_bytes(data: bytearray) -> 'Fields':
        """
        Deserialize bytes into a Fields instance.

        Args:
            data (bytearray): The byte data to deserialize.

        Returns:
            Fields: The deserialized Fields instance.
        """
        seek = 0
        total_length = int.from_bytes(data[seek:seek + SOCKET_FULL_LENGTH_SIZE], byteorder="big")
        if total_length + SOCKET_FULL_LENGTH_SIZE != len(data):
            raise ValueError("Data length does not match the specified total length.")
        seek += SOCKET_FULL_LENGTH_SIZE

        fields = []
        while seek + SOCKET_FIELD_LENGTH_SIZE < len(data):
            field_length = int.from_bytes(data[seek:seek + SOCKET_FIELD_LENGTH_SIZE], byteorder="big")
            seek += SOCKET_FIELD_LENGTH_SIZE

            field_type_byte = data[seek]
            field_type = FieldType.from_byte(field_type_byte)
            seek += 1

            field_value = data[seek:seek + field_length - 1]  
            seek += field_length - 1
            field = Field(field_type, field_value)
            fields.append(field)

        return Fields(fields)
            
    def consume_field(self, type_: FieldType | None = None) -> Field | None:
        """
        Consume and return the next Field in the collection.

        Returns:
            Field | None: The next Field if available, otherwise None.
        """
        if self.seek_ >= len(self.fields):
            return None

        field = self.fields[self.seek_]
        self.seek_ += 1

        if type_ is not None and field.type_ != type_:
            return None

        return field

    def seek(self, position: int) -> None:
        """
        Set the current seek position.

        Args:
            position (int): The position to seek to.
        """
        if not (0 <= position <= len(self.fields)):
            raise ValueError(f"Seek position {position} out of range.")

        self.seek_ = position
    
    def __str__(self) -> str:
        return f"Fields[{', '.join(str(field) for field in self.fields)}]"

class FieldsBuilder:
    """
    Builder class for constructing Fields instances.
    """

    fields: list[Field]

    def __init__(self) -> None:
        self.fields = []

    def add_int_field(self, value: int) -> 'FieldsBuilder':
        """
        Add an INT field.

        Args:
            value (int): The integer value to add.

        Returns:
            FieldsBuilder: The current instance for chaining.
        """
        field = Field(FieldType.INT, value)
        self.fields.append(field)
        return self
    
    def add_raw_field(self, value: bytearray | bytes) -> 'FieldsBuilder':
        """
        Add a RAW field.

        Args:
            value (bytearray | bytes): The raw byte data to add.

        Returns:
            FieldsBuilder: The current instance for chaining.
        """
        field = Field(FieldType.RAW, value)
        self.fields.append(field)
        return self

    def add_text_field(self, value: str) -> 'FieldsBuilder':
        """
        Add a TEXT field.

        Args:
            value (str): The text string to add.

        Returns:
            FieldsBuilder: The current instance for chaining.
        """
        field = Field(FieldType.TEXT, value)
        self.fields.append(field)
        return self

    def build(self) -> Fields:
        """
        Build and return the Fields instance.

        Returns:
            Fields: The constructed Fields instance.
        """
        return Fields(self.fields)
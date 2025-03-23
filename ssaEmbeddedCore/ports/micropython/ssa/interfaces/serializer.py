class Serializer:
    """
    Interface for serialization and deserialization.
    """

    def dump(self, obj, stream):
        """
        Serialize obj and write it to a stream.

        Args:
            obj: object to serialize
            stream: file-like object to write to
        """
        pass

    def dumps(self, obj):
        """
        Serialize obj to a string.

        Args:
            obj: object to serialize

        Returns:
            str: String representation of the object
        """
        pass

    def load(self, stream):
        """
        Deserialize obj from a stream.

        Args:
            stream: file-like object to read from

        Returns:
            object: Deserialized object
        """
        pass

    def loads(self, string):
        """
        Deserialize obj from a string.

        Args:
            string: string to deserialize

        Returns:
            object: Deserialized object
        """
        pass

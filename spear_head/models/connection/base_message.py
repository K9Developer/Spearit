from models.connection.connection import Connection

class BaseMessage:

    @staticmethod
    def handle(conn: Connection) -> bool:
        """
        Handle the message for the given connection.
        Args:
            conn (Connection): The connection to handle the message for.
        Returns:
            bool: True if the message was handled successfully, False otherwise.
        """
        raise NotImplementedError("Handle method must be implemented by subclasses.")
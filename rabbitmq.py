import json
import logging
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv

import pika
from pika.exceptions import AMQPConnectionError, AMQPChannelError
import os

load_dotenv()

class RabbitMQDispatcher:
    """
    RabbitMQ dispatcher for sending parsed JSON messages from the chatbot
    to the sehatin-be-message Laravel service.
    """

    def __init__(
        self,
        host: str = os.getenv("RABBITMQ_HOST", "localhost"),
        port: int = int(os.getenv("RABBITMQ_PORT", 5672)),
        username: str = os.getenv("RABBITMQ_USER", "guest"),
        password: str = os.getenv("RABBITMQ_PASSWORD", "guest"),
        virtual_host: str = "/",
        exchange: str = "",
        queue: str = "chatbot-messages",
        max_retries: int = 3,
        retry_delay: int = 2
    ):
        """
        Initialize the RabbitMQ dispatcher.

        Args:
            host: RabbitMQ server hostname
            port: RabbitMQ server port
            username: RabbitMQ username
            password: RabbitMQ password
            virtual_host: RabbitMQ virtual host
            exchange: Exchange name (empty for default)
            queue: Queue name to send messages to
            max_retries: Maximum number of connection retry attempts
            retry_delay: Delay in seconds between retry attempts
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.virtual_host = virtual_host
        self.exchange = exchange
        self.queue = queue
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.connection = None
        self.channel = None
        self.logger = logging.getLogger(__name__)

        # Set up initial connection
        self.connect()

    def connect(self) -> bool:
        """
        Establish connection to RabbitMQ server.

        Returns:
            bool: True if connection established successfully, False otherwise
        """
        retry_count = 0

        while retry_count < self.max_retries:
            try:
                # Close existing connections if any
                if self.connection and self.connection.is_open:
                    self.connection.close()

                # Create connection parameters
                credentials = pika.PlainCredentials(self.username, self.password)
                parameters = pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    virtual_host=self.virtual_host,
                    credentials=credentials,
                    heartbeat=600,
                    blocked_connection_timeout=300
                )

                # Establish connection
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()

                # Declare queue (creates if doesn't exist)
                self.channel.queue_declare(queue=self.queue, durable=True)

                self.logger.info(f"Successfully connected to RabbitMQ at {self.host}:{self.port}")
                return True

            except (AMQPConnectionError, AMQPChannelError) as e:
                retry_count += 1
                self.logger.warning(
                    f"Failed to connect to RabbitMQ (attempt {retry_count}/{self.max_retries}): {str(e)}"
                )

                if retry_count < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error("Max retries reached. Failed to connect to RabbitMQ.")
                    return False

    def send_message(self, data: Dict[str, Any], routing_key: Optional[str] = None) -> bool:
        """
        Serialize and send a JSON message to RabbitMQ.

        Args:
            data: Dictionary data to be serialized as JSON
            routing_key: Optional routing key, defaults to queue name if not provided

        Returns:
            bool: True if message sent successfully, False otherwise
        """
        if routing_key is None:
            routing_key = self.queue

        # Ensure connection is alive
        if not self.connection or not self.connection.is_open:
            if not self.connect():
                self.logger.error("Cannot send message: Not connected to RabbitMQ")
                return False

        try:
            # Convert data to JSON
            message = json.dumps(data)

            # Publish message
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=routing_key,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type='application/json'
                )
            )

            self.logger.debug(f"Message sent to queue '{routing_key}': {message}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")

            # Try to reconnect and send again
            if not isinstance(e, (AMQPConnectionError, AMQPChannelError)):
                return False

            if self.connect():
                try:
                    message = json.dumps(data)
                    self.channel.basic_publish(
                        exchange=self.exchange,
                        routing_key=routing_key,
                        body=message,
                        properties=pika.BasicProperties(
                            delivery_mode=2,
                            content_type='application/json'
                        )
                    )
                    return True
                except Exception as retry_e:
                    self.logger.error(f"Failed to send message after reconnection: {str(retry_e)}")

            return False

    def close(self):
        """
        Close the RabbitMQ connection.
        """
        if self.connection and self.connection.is_open:
            self.connection.close()
            self.logger.info("RabbitMQ connection closed")
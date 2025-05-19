import pika

def dispatch_to_queue(json_data, queue_name='recommendations-queue', rabbitmq_host='localhost'):
    """
    Dispatch JSON data to a RabbitMQ queue.

    :param json_data: JSON data to be dispatched (as a string)
    :param queue_name: Name of the RabbitMQ queue
    :param rabbitmq_host: RabbitMQ host address
    """
    # Connect to RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()

    # Declare the queue
    channel.queue_declare(queue=queue_name, durable=True)

    # Publish the message
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json_data,
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
        )
    )

    print(f"JSON dispatched to queue '{queue_name}': {json_data}")

    # Close the connection
    connection.close()

# Example usage
json_data = '{"key": "value"}'  # Replace with your JSON string
dispatch_to_queue(json_data)
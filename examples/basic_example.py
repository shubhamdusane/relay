"""
Relay - Core Example
Demonstrates basic Relay functionality for reliable message delivery between agents.
"""

from relay import Relay, Channel, Message, DeliveryReceipt

def main():
    # Initialize the relay
    relay = Relay(name="agent-relay")

    # Create channels
    channel = Channel(
        name="task-updates",
        type="persistent",
        max_size=1000
    )
    relay.create_channel(channel)

    # Publish a message
    msg = Message(
        task_id="task-001",
        status="completed",
        result={"output": "processed successfully"}
    )
    receipt = relay.publish("task-updates", msg)

    # Subscribe to messages
    def handle_message(message):
        print(f"Received: {message.task_id} - {message.status}")

    relay.subscribe("task-updates", handle_message)

    # Deliver pending messages
    delivered = relay.deliver("task-updates")

    print(f"Relay: {relay.name}")
    print(f"Channels: {relay.channel_count}")
    print(f"Message delivered: {receipt.delivered}")
    print(f"Pending deliveries: {delivered}")

if __name__ == "__main__":
    main()

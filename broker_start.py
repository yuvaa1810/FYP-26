import asyncio
from amqtt.broker import Broker

config = {
    'listeners': {'default': {'type': 'tcp', 'bind': '0.0.0.0:1883'}},
    'sys_interval': 10,
    'auth': {'allow-anonymous': True}
}

async def start_broker():
    broker = Broker(config)
    await broker.start()

if __name__ == '__main__':
    print("🚀 Local MQTT Broker Starting on Port 1883...")
    asyncio.get_event_loop().run_until_complete(start_broker())
    asyncio.get_event_loop().run_forever()
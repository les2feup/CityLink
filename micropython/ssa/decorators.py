import asyncio
from typing import Any, Callable, Tuple
from ssa.core import SSA, SSA_Property

def ssa_property_task(property_name: str, period_ms: int, retain: bool = False, qos: int = 0):
    """! Decorator to handle the publication of a property to the broker
        @param property: The property to publish
        @param period_ms: The period in milliseconds to publish the property

        The decorated function will be called in a loop, sleeping for the specified period
        after each call.
        The result of the decorated function will be published (on change) to the broker
        with the specified property name.
        If the property has an event associated with it, the event will be checked and published
        (if triggered) each cycle after the property is published.

        The decorated function should return the value to be published.
        The decorated function signature should be:
            async def func() -> Any

        Note: See ssa_main decorator documentation for example usage
    """
    def decorator(func: Callable[[], Any]):
        def wrapper():
            ssa_instance = SSA()
            if property_name not in ssa_instance.__properties:
                ssa_instance.__properties[property_name] = SSA_Property(None)

            while True:
                property: SSA_Property = ssa_instance.__properties[property_name]
                previous = property.value
                result = await func()

                if previous != result:
                    ssa_instance.__properties[property_name].value = result
                    ssa_instance.__publish(f"properties/{property_name}", f"{result}",
                                           retain=retain, qos=qos)

                is_event, event_value = property.check_event()
                if is_event:
                    ssa_instance.__publish(f"events/{property.event_name}", f"{event_value}")

                #TODO: improve task periodicity by taking into account the time taken to execute the loop
                await asyncio.sleep_ms(period_ms)
            
        return wrapper
    return decorator

def ssa_event_task(event: str, period_ms: int, retain: bool = False, qos: int = 0):
    """! Decorator to handle the publication of an event to the broker
        @param event: The event to publish
        @param period_ms: The period in milliseconds to check for event occurrence

        The decorated function will be called in a loop, sleeping for the specified period
        after each call.

        The decorated function should return a tuple of two values:
            async def func() -> Tuple[bool, Any]
            The first value should be a boolean indicating whether the event has occurred.
            The second value should be the result to publish to the broker in case of event occurrence.

        Note: See ssa_main decorator documentation for example usage
    """
    def decorator(func: Callable[[], Tuple[bool, Any]]):
        def wrapper():
            ssa_instance = SSA()

            while True:
                trigger_event, result = await func()
                if trigger_event:
                    ssa_instance.__publish(f"events/{event}", f"{result}",
                                           retain=retain, qos=qos)

                #TODO: improve task periodicity by taking into account the time taken to execute the loop
                await asyncio.sleep_ms(period_ms)

        return wrapper
    return decorator

def ssa_main(init_func):
    """! Decorator to create the main function of the application
        @param init_func: A function that takes an SSA instance as an argument
        and sets up the application property/event handlers and action callbacks.
        The function signature should be:
            def func(ssa: SSA) -> None

        The decorated function will be wrapped in an async function that will
        create an SSA instance, run the init function, connect to the broker
        and start the main loop.

        The code flow will be:
        1. Create an SSA instance
        2. Run the init function
        3. Connect to the broker
        4. Execute the SSA Network Registration process
        5. Start the main loop and service incoming messages and run the registered handlershandlers

        example usage:

            @ssa_property_task("value", 2000)
            async def example_prop_handler():
                return random.randint(0, 100)

            @ssa_event_handler("event", 2000)
            async def example_event_handler():
                return random.randint(0, 100) > 50, "Event occurred"

            def example_action_callback(msg: str):
                print(f"Action triggered with message: {msg}")

            @ssa_main
            def init(ssa: SSA):
                ssa.register_handler(example_prop_handler)
                ssa.register_handler(example_event_handler)
                ssa.action_callback("action", example_action_callback)

            if __name__ == "__main__":
                init()
    """
    def main_wrapper():
        async def ssa_entry_point():
            ssa_instance = SSA()

            try:
                init_func(ssa_instance)
            except Exception as e:
                raise Exception(f"[ERROR] Failed to run initial setup: {e}")

            try:
                ssa_instance.__connect("Goodbye")
            except Exception as e:
                raise Exception(f"[ERROR] SSA connection failed: {e}") from e

            await ssa_instance.__main_loop()

        asyncio.run(ssa_entry_point())
    return main_wrapper

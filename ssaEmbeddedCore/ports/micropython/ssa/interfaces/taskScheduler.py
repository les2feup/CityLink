class TaskScheduler:
    """Abstract base class for task schedulers."""

    def _start_scheduler(self, main_task):
        """Launch the runtime and start running all registered tasks."""
        raise NotImplementedError("Subclasses must implement launch()")

    def task_create(self, task_id, task_func, period_ms=0):
        """
        Register a task for execution.

        Associates a unique task identifier with a callable that encapsulates the task's logic.
        Subclasses must override this method to provide the actual task scheduling or execution
        mechanism.

        Args:
            task_id: A unique identifier for the task.
            task_func: A callable implementing the task's functionality.
            period_ms: The period in milliseconds between consecutive executions of the task.
                      If set to 0 (default), the task will execute only once (one-shot task).
                      If greater than 0, the task will execute repeatedly at the specified interval.

        Raises:
            NotImplementedError: Always, as this method must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement rt_task_create()")

    def task_cancel(self, task_id):
        """Cancel a registered task.

        Cancel the task identified by the given task_id. This method serves as a stub and must be overridden by subclasses to implement task cancellation. Calling this method directly will raise a NotImplementedError.

        Args:
            task_id: The identifier of the task to cancel.
        """
        raise NotImplementedError("Subclasses must implement rt_task_cancel()")

    async def task_sleep_s(self, s):
        """Asynchronously sleep for the specified number of seconds.

        This abstract method must be implemented by subclasses to pause
        execution asynchronously for the given duration.

        Args:
            s (int | float): The sleep duration in seconds.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses must implement rt_task_sleep_s()")

    async def task_sleep_ms(self, ms):
        """
        Asynchronously pause execution for a specified number of milliseconds.

        This coroutine should suspend execution for the provided duration. Subclasses
        must override this method to implement the actual sleep behavior.

        Args:
            ms: Duration to sleep in milliseconds.

        Raises:
            NotImplementedError: If the method is not overridden by a subclass.
        """
        raise NotImplementedError("Subclasses must implement rt_task_sleep_ms()")

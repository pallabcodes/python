from abc import ABC, abstractmethod


class Lockable(ABC):
    @abstractmethod
    def lock(self):
        pass

    @abstractmethod
    def unlock(self):
        pass


class NonLocking(Lockable):
    def lock(self):
        print("Door does not lock - ignoring")

    def unlock(self):
        print("Door cannot unlock because it cannot lock")


class Password(Lockable):
    def lock(self):
        print("Door locked using password!")

    def unlock(self):
        print("Door unlocked using password!")


class KeyCard(Lockable):
    def lock(self):
        pass

    def unlock(self):
        pass


class Openable(ABC):
    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def close(self):
        pass


class Standard(Openable):
    def open(self):
        print("Pushing door open")

    def close(self):
        print("Pulling door closed")


class Revolving(Openable):
    def open(self):
        pass

    def close(self):
        pass


class Sliding(Openable):
    def open(self):
        pass

    def close(self):
        pass


class Door(ABC):
    def __init__(self):
        # Using underscore as convention for private members in Python
        self._lock_behavior = None
        self._open_behavior = None

    def set_lock_behavior(self, lock_behavior):
        self._lock_behavior = lock_behavior

    def set_open_behavior(self, open_behavior):
        self._open_behavior = open_behavior

    def perform_lock(self):
        self._lock_behavior.lock()

    def perform_unlock(self):
        self._lock_behavior.unlock()

    def perform_open(self):
        self._open_behavior.open()

    def perform_close(self):
        self._open_behavior.close()

    def get_dimensions(self):
        return 5


class ClosetDoor(Door):
    pass


class ExternalDoor(Door):
    pass


class SafeDepositDoor(Door):
    pass


class SlidingDoor(Door):
    pass


# Initialize door
c = ClosetDoor()

# Set behaviors
c.set_open_behavior(Standard())
c.set_lock_behavior(NonLocking())

# Invoke behaviors
c.perform_open()
c.perform_close()
c.perform_lock()
c.perform_unlock()

# Upgrade the door to be password protected
c.set_lock_behavior(Password())
c.perform_lock()
c.perform_unlock()

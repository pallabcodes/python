from enum import Enum


class Brightness(Enum):
    UNKNOWN = 0
    BRIGHT = 1
    DIM = 2


class Service(Enum):
    UNKNOWN = 0
    HULU = 1
    NETFLIX = 2
    HBO = 3


class SmartHomeSubSystem:

    def __init__(self):
        self.brightness = Brightness.UNKNOWN
        self.temperature = 19
        self.is_security_armed = False
        self.streaming_service = Service.UNKNOWN

    def set_brightness(self, brightness):
        self.brightness = brightness

    def set_temperature(self, temperature):
        self.temperature = temperature

    def set_is_security_armed(self, is_security_armed):
        self.is_security_armed = is_security_armed

    def set_streaming_service(self, streaming_service):
        self.streaming_service = streaming_service

    def get_status(self):
        return (
            f"Brightness: {self.brightness.name}, "
            f"Temperature: {self.temperature}°C, "
            f"Security Armed: {self.is_security_armed}, "
            f"Streaming Service: {self.streaming_service.name}"
        )


class SmartHomeFacade:

    def __init__(self, smart_home):
        self.smart_home = smart_home

    def set_movie_mode(self):
        self.smart_home.set_brightness(Brightness.DIM)
        self.smart_home.set_temperature(21)
        self.smart_home.set_is_security_armed(False)
        self.smart_home.set_streaming_service(Service.NETFLIX)
        print("\n[Movie Mode Activated]")
        print(self.smart_home.get_status())

    def set_focus_mode(self):
        self.smart_home.set_brightness(Brightness.BRIGHT)
        self.smart_home.set_temperature(22)
        self.smart_home.set_is_security_armed(True)
        self.smart_home.set_streaming_service(Service.UNKNOWN)
        print("\n[Focus Mode Activated]")
        print(self.smart_home.get_status())


# Test
f = SmartHomeFacade(SmartHomeSubSystem())
f.set_movie_mode()
f.set_focus_mode()
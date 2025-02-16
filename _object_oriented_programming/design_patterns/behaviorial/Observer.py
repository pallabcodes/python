from abc import ABC, abstractmethod


class Subject(ABC):
    @abstractmethod
    def register_observer(self, observer):
        pass

    @abstractmethod
    def remove_observer(self, observer):
        pass

    @abstractmethod
    def notify_observers(self):
        pass


class ConcreteSubject(Subject):
    def __init__(self):
        self._observers = []
        self._value = 0

    def register_observer(self, observer):
        self._observers.append(observer)

    def remove_observer(self, observer):
        self._observers.remove(observer)

    def notify_observers(self):
        for observer in self._observers:
            observer.update(self._value)

    def set_value(self, value):
        self._value = value
        self.notify_observers()


class Observer(ABC):
    @abstractmethod
    def update(self, value):
        pass


class ConcreteObserver(Observer):
    def __init__(self, subject):
        self._subject = subject
        self._value = None
        self._subject.register_observer(self)

    def update(self, value):
        self._value = value


#***********Scenario Implementation************#


class Store(ABC):
    @abstractmethod
    def add_customer(self, customer):
        pass

    @abstractmethod
    def remove_customer(self, customer):
        pass

    @abstractmethod
    def notify_customers(self):
        pass

    @abstractmethod
    def update_quantity(self, quantity):
        pass


class BookStore(Store):
    def __init__(self):
        self._customers = []
        self._stock_quantity = 0

    def add_customer(self, customer):
        self._customers.append(customer)

    def remove_customer(self, customer):
        self._customers.remove(customer)

    def notify_customers(self):
        for customer in self._customers:
            customer.update(self._stock_quantity)

    def update_quantity(self, quantity):
        self._stock_quantity = quantity
        self.notify_customers()


class Customer(ABC):
    @abstractmethod
    def update(self, stock_quantity):
        pass


class BookCustomer(Customer):
    def __init__(self, store):
        self._store = store
        self._observed_stock_quantity = None
        self._store.add_customer(self)

    def update(self, stock_quantity):
        self._observed_stock_quantity = stock_quantity
        if stock_quantity > 0:
            print("Hello, A book you are interested in is back in stock!")


store = BookStore()
customer1 = BookCustomer(store)
customer2 = BookCustomer(store)

# Initially, the book is out of stock
print("Setting stock to 0.")
store.update_quantity(0)

# The book comes back in stock
print("Setting stock to 5.")
store.update_quantity(5)

# Remove customer1 from the notification list
store.remove_customer(customer1)

# Simulate the situation where the stock changes again
print("\nSetting stock to 2.")
store.update_quantity(2)

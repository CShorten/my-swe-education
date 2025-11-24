Quick Notes

- Inside the Hexagon, Outside the Hexagon

# List
1. Singleton
Ensures a class has only one instance throughout the application and provides a global point of access to it. Commonly used for configuration managers, logging, or database connections.
2. Factory
Provides an interface for creating objects without specifying their exact classes. The factory method decides which class to instantiate based on input parameters or configuration.
3. Observer
Defines a one-to-many dependency where when one object (subject) changes state, all its dependents (observers) are notified automatically. Used extensively in event handling systems and MVC frameworks.
4. Strategy
Defines a family of algorithms, encapsulates each one, and makes them interchangeable. The strategy lets the algorithm vary independently from clients that use it. Great for payment processors, sorting algorithms, or validation rules.
5. Decorator
Allows you to add new functionality to objects dynamically by wrapping them in decorator objects. This provides a flexible alternative to subclassing for extending functionality.
6. Adapter
Converts the interface of a class into another interface that clients expect. It lets classes work together that couldn't otherwise because of incompatible interfaces. Think of it like a power plug adapter.
7. Dependency Injection
A technique where an object receives its dependencies from external sources rather than creating them itself. This promotes loose coupling and makes testing easier by allowing mock dependencies.
8. Model-View-Controller (MVC)
Separates an application into three interconnected components: Model (data), View (presentation), and Controller (logic). This separation makes applications more modular and maintainable.

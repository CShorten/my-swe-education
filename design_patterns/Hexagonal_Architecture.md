# Hexagonal Architecture in Go: A Complete Guide

## Executive Summary

Hexagonal Architecture, also known as Ports and Adapters pattern, provides a robust framework for building maintainable, testable, and loosely coupled applications in Go. This architecture isolates business logic from external concerns like databases, web frameworks, and third-party services, enabling greater flexibility and easier testing. The pattern is particularly well-suited to Go's interface-driven design philosophy and emphasis on composition over inheritance.

## What is Hexagonal Architecture?

Hexagonal Architecture was introduced by Alistair Cockburn to address the common problem of tightly coupled code where business logic becomes entangled with infrastructure concerns. The "hexagon" represents the application's core business logic, while the edges represent ports (interfaces) through which the application communicates with the outside world via adapters.

### Core Principles

**Dependency Inversion**: Dependencies flow inward toward the business logic, not outward toward infrastructure.

**Port and Adapter Pattern**: Ports define what the application needs (interfaces), while adapters implement how external systems fulfill these needs.

**Testability**: Business logic can be tested in isolation without external dependencies.

**Technology Independence**: The core business logic remains unaware of specific databases, frameworks, or external services.

## Architecture Components

### The Domain Layer (Core)

The innermost layer contains pure business logic, entities, and domain services. This layer has no dependencies on external frameworks or infrastructure.

```go
// Domain entity
type User struct {
    ID       string
    Email    string
    Name     string
    Password string
    CreatedAt time.Time
}

// Domain service
type UserService struct {
    userRepo UserRepository
}

func (s *UserService) CreateUser(email, name, password string) (*User, error) {
    // Business logic validation
    if !isValidEmail(email) {
        return nil, errors.New("invalid email format")
    }
    
    user := &User{
        ID:        generateID(),
        Email:     email,
        Name:      name,
        Password:  hashPassword(password),
        CreatedAt: time.Now(),
    }
    
    return s.userRepo.Save(user)
}
```

### Ports (Interfaces)

Ports define contracts for communication between the core and external systems. They represent what the application needs, not how it's implemented.

```go
// Primary port (driven by external actors)
type UserHandler interface {
    CreateUser(w http.ResponseWriter, r *http.Request)
    GetUser(w http.ResponseWriter, r *http.Request)
}

// Secondary port (drives external systems)
type UserRepository interface {
    Save(user *User) (*User, error)
    FindByID(id string) (*User, error)
    FindByEmail(email string) (*User, error)
}

type EmailService interface {
    SendWelcomeEmail(user *User) error
}
```

### Adapters

Adapters implement the ports, handling the technical details of external system integration.

```go
// HTTP adapter (primary adapter)
type HTTPUserHandler struct {
    userService *UserService
}

func (h *HTTPUserHandler) CreateUser(w http.ResponseWriter, r *http.Request) {
    var req CreateUserRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid JSON", http.StatusBadRequest)
        return
    }
    
    user, err := h.userService.CreateUser(req.Email, req.Name, req.Password)
    if err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }
    
    json.NewEncoder(w).Encode(user)
}

// Database adapter (secondary adapter)
type PostgreSQLUserRepository struct {
    db *sql.DB
}

func (r *PostgreSQLUserRepository) Save(user *User) (*User, error) {
    query := `INSERT INTO users (id, email, name, password, created_at) 
              VALUES ($1, $2, $3, $4, $5)`
    
    _, err := r.db.Exec(query, user.ID, user.Email, user.Name, 
                       user.Password, user.CreatedAt)
    if err != nil {
        return nil, err
    }
    
    return user, nil
}

func (r *PostgreSQLUserRepository) FindByID(id string) (*User, error) {
    query := `SELECT id, email, name, password, created_at 
              FROM users WHERE id = $1`
    
    var user User
    err := r.db.QueryRow(query, id).Scan(&user.ID, &user.Email, 
                                        &user.Name, &user.Password, 
                                        &user.CreatedAt)
    if err != nil {
        return nil, err
    }
    
    return &user, nil
}
```

## Project Structure

A typical Go project using Hexagonal Architecture might be organized as follows:

```
project/
├── cmd/
│   └── api/
│       └── main.go
├── internal/
│   ├── domain/
│   │   ├── user.go
│   │   └── user_service.go
│   ├── ports/
│   │   ├── user_handler.go
│   │   ├── user_repository.go
│   │   └── email_service.go
│   └── adapters/
│       ├── http/
│       │   └── user_handler.go
│       ├── postgres/
│       │   └── user_repository.go
│       └── smtp/
│           └── email_service.go
├── pkg/
└── go.mod
```

## Dependency Injection and Wiring

The application's main function or a dedicated container handles dependency injection:

```go
func main() {
    // Infrastructure setup
    db, err := sql.Open("postgres", connectionString)
    if err != nil {
        log.Fatal(err)
    }
    defer db.Close()
    
    // Create adapters
    userRepo := &PostgreSQLUserRepository{db: db}
    emailService := &SMTPEmailService{
        host: "smtp.gmail.com",
        port: 587,
    }
    
    // Create domain services
    userService := &UserService{
        userRepo:     userRepo,
        emailService: emailService,
    }
    
    // Create handlers
    userHandler := &HTTPUserHandler{
        userService: userService,
    }
    
    // Setup routes
    http.HandleFunc("/users", userHandler.CreateUser)
    http.HandleFunc("/users/", userHandler.GetUser)
    
    log.Fatal(http.ListenAndServe(":8080", nil))
}
```

## Testing Benefits

Hexagonal Architecture makes testing significantly easier by allowing you to test business logic in isolation:

```go
func TestUserService_CreateUser(t *testing.T) {
    // Arrange
    mockRepo := &MockUserRepository{}
    mockEmail := &MockEmailService{}
    service := &UserService{
        userRepo:     mockRepo,
        emailService: mockEmail,
    }
    
    // Act
    user, err := service.CreateUser("test@example.com", "John Doe", "password123")
    
    // Assert
    assert.NoError(t, err)
    assert.Equal(t, "test@example.com", user.Email)
    assert.True(t, mockRepo.SaveCalled)
    assert.True(t, mockEmail.SendWelcomeEmailCalled)
}

// Mock implementations for testing
type MockUserRepository struct {
    SaveCalled bool
    users      map[string]*User
}

func (m *MockUserRepository) Save(user *User) (*User, error) {
    m.SaveCalled = true
    if m.users == nil {
        m.users = make(map[string]*User)
    }
    m.users[user.ID] = user
    return user, nil
}
```

## Advanced Patterns

### Command Query Responsibility Segregation (CQRS)

You can combine Hexagonal Architecture with CQRS for more complex scenarios:

```go
type UserCommandHandler interface {
    CreateUser(cmd CreateUserCommand) error
    UpdateUser(cmd UpdateUserCommand) error
}

type UserQueryHandler interface {
    GetUser(query GetUserQuery) (*User, error)
    ListUsers(query ListUsersQuery) ([]*User, error)
}
```

### Event-Driven Architecture

Integrate domain events within the hexagonal structure:

```go
type DomainEvent interface {
    EventType() string
    OccurredAt() time.Time
}

type UserCreatedEvent struct {
    UserID    string
    Email     string
    OccurredAt time.Time
}

type EventPublisher interface {
    Publish(event DomainEvent) error
}
```

## Go-Specific Considerations

### Interface Segregation

Go's implicit interface satisfaction makes it easy to create focused, single-purpose interfaces:

```go
type UserFinder interface {
    FindByID(id string) (*User, error)
}

type UserSaver interface {
    Save(user *User) (*User, error)
}

// Combine interfaces when needed
type UserRepository interface {
    UserFinder
    UserSaver
}
```

### Error Handling

Leverage Go's explicit error handling within the architecture:

```go
type DomainError struct {
    Code    string
    Message string
    Cause   error
}

func (e *DomainError) Error() string {
    return fmt.Sprintf("%s: %s", e.Code, e.Message)
}

var (
    ErrUserNotFound = &DomainError{Code: "USER_NOT_FOUND", Message: "user not found"}
    ErrInvalidEmail = &DomainError{Code: "INVALID_EMAIL", Message: "invalid email format"}
)
```

### Context Propagation

Use Go's context package for request-scoped data and cancellation:

```go
type UserService struct {
    userRepo UserRepository
}

func (s *UserService) CreateUser(ctx context.Context, email, name, password string) (*User, error) {
    if err := ctx.Err(); err != nil {
        return nil, err
    }
    
    // Business logic...
    return s.userRepo.Save(ctx, user)
}
```

## Benefits and Trade-offs

### Benefits

**Maintainability**: Clear separation of concerns makes code easier to understand and modify.

**Testability**: Business logic can be tested without external dependencies.

**Flexibility**: Easy to swap implementations or add new interfaces.

**Technology Independence**: Core business logic remains stable as technology changes.

**Parallel Development**: Teams can work on different adapters simultaneously.

### Trade-offs

**Complexity**: Additional abstraction layers can increase initial complexity.

**Over-engineering**: May be overkill for simple applications.

**Learning Curve**: Team members need to understand the architectural patterns.

**Initial Setup Time**: More boilerplate code compared to simpler architectures.

## When to Use Hexagonal Architecture

Hexagonal Architecture is most beneficial for:

- Applications with complex business logic
- Systems requiring high testability
- Projects expecting frequent technology changes
- Applications with multiple interfaces (web, CLI, API)
- Long-term projects where maintainability is crucial

Consider simpler alternatives for:

- Simple CRUD applications
- Prototypes or proof-of-concepts
- Small, short-lived projects
- Applications with minimal business logic

## Conclusion

Hexagonal Architecture provides a solid foundation for building maintainable Go applications by enforcing clear boundaries between business logic and infrastructure concerns. While it introduces additional complexity, the benefits of testability, flexibility, and maintainability make it valuable for medium to large-scale applications. Go's interface system and emphasis on composition make it particularly well-suited for implementing this architectural pattern.

The key to success with Hexagonal Architecture is understanding when to apply it and ensuring the team is comfortable with the additional abstractions. When implemented thoughtfully, it creates a codebase that can evolve gracefully with changing business requirements and technology landscapes.

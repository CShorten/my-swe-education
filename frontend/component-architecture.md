# React Component Architecture Best Practices

## 1. Component Types

### Presentational Components
- Focus solely on UI rendering
- Receive data via props
- No direct state management
- Highly reusable

```jsx
function UserCard({ name, email, avatar }) {
  return (
    <div className="card">
      <img src={avatar} alt={name} />
      <h3>{name}</h3>
      <p>{email}</p>
    </div>
  );
}
```

### Container Components
- Handle business logic and state
- Pass data to presentational components
- Manage API calls and side effects
- Focus on how things work

```jsx
function UserContainer() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUser().then(data => {
      setUser(data);
      setLoading(false);
    });
  }, []);

  if (loading) return <Spinner />;
  return <UserCard {...user} />;
}
```

## 2. Component Composition

### Higher-Order Components (HOCs)
- Wrap components to add functionality
- Follow composition over inheritance
- Keep logic reusable

```jsx
function withAuth(WrappedComponent) {
  return function AuthWrapper(props) {
    const isAuthenticated = useAuth();
    
    if (!isAuthenticated) {
      return <Navigate to="/login" />;
    }
    
    return <WrappedComponent {...props} />;
  };
}
```

### Compound Components
- Create flexible component APIs
- Share state implicitly
- Improve component flexibility

```jsx
function Accordion({ children }) {
  const [activeIndex, setActiveIndex] = useState(0);
  
  return (
    <AccordionContext.Provider value={{ activeIndex, setActiveIndex }}>
      {children}
    </AccordionContext.Provider>
  );
}

Accordion.Item = function AccordionItem({ children, index }) {
  const { activeIndex } = useContext(AccordionContext);
  const isActive = activeIndex === index;
  
  return (
    <div className={`accordion-item ${isActive ? 'active' : ''}`}>
      {children}
    </div>
  );
};
```

## 3. Directory Structure

```
components/
  ├── common/              # Shared components
  │   ├── Button/
  │   │   ├── Button.jsx
  │   │   ├── Button.test.jsx
  │   │   └── Button.styles.js
  │   └── Input/
  ├── features/           # Feature-specific components
  │   ├── Authentication/
  │   └── Dashboard/
  └── layouts/            # Layout components
      ├── MainLayout/
      └── AuthLayout/
```

## 4. Component Design Principles

### Single Responsibility
- Each component should do one thing well
- Split components when they exceed 250 lines
- Separate concerns clearly

```jsx
// Bad: Multiple responsibilities
function UserProfile() {
  const [user, setUser] = useState(null);
  const [posts, setPosts] = useState([]);
  
  // Fetching user data
  // Fetching posts
  // Handling forms
  // Complex UI rendering
}

// Good: Separated responsibilities
function UserProfile() {
  return (
    <div>
      <UserInfo />
      <UserPosts />
      <UserSettings />
    </div>
  );
}
```

### Props Interface
- Keep props interface minimal
- Use prop types or TypeScript
- Provide meaningful defaults

```tsx
interface ButtonProps {
  variant?: 'primary' | 'secondary';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}

function Button({
  variant = 'primary',
  size = 'medium',
  disabled = false,
  children,
  onClick
}: ButtonProps) {
  // Component implementation
}
```

## 5. Error Handling

```jsx
function ComponentWithErrorBoundary() {
  return (
    <ErrorBoundary fallback={<ErrorUI />}>
      <ComplexComponent />
    </ErrorBoundary>
  );
}

class ErrorBoundary extends React.Component {
  state = { hasError: false };
  
  static getDerivedStateFromError() {
    return { hasError: true };
  }
  
  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}
```

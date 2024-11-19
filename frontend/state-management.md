# React State Management Guide

## 1. Local State Management

### useState Hook
```jsx
function Counter() {
  const [count, setCount] = useState(0);
  
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>Increment</button>
    </div>
  );
}
```

### useReducer Hook
```jsx
const reducer = (state, action) => {
  switch (action.type) {
    case 'increment':
      return { count: state.count + 1 };
    case 'decrement':
      return { count: state.count - 1 };
    default:
      return state;
  }
};

function ComplexCounter() {
  const [state, dispatch] = useReducer(reducer, { count: 0 });
  
  return (
    <div>
      <p>Count: {state.count}</p>
      <button onClick={() => dispatch({ type: 'increment' })}>+</button>
      <button onClick={() => dispatch({ type: 'decrement' })}>-</button>
    </div>
  );
}
```

## 2. Context API

### Creating and Using Context
```jsx
const ThemeContext = createContext('light');

function ThemeProvider({ children }) {
  const [theme, setTheme] = useState('light');
  
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

function ThemedButton() {
  const { theme, setTheme } = useContext(ThemeContext);
  
  return (
    <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
      Current theme: {theme}
    </button>
  );
}
```

### Context with Reducer
```jsx
const UserContext = createContext();

const userReducer = (state, action) => {
  switch (action.type) {
    case 'login':
      return { ...state, user: action.payload, isAuthenticated: true };
    case 'logout':
      return { ...state, user: null, isAuthenticated: false };
    default:
      return state;
  }
};

function UserProvider({ children }) {
  const [state, dispatch] = useReducer(userReducer, {
    user: null,
    isAuthenticated: false
  });
  
  return (
    <UserContext.Provider value={{ state, dispatch }}>
      {children}
    </UserContext.Provider>
  );
}
```

## 3. State Management Libraries

### Redux Toolkit Example
```jsx
// Store setup
import { configureStore, createSlice } from '@reduxjs/toolkit';

const counterSlice = createSlice({
  name: 'counter',
  initialState: { value: 0 },
  reducers: {
    increment: state => { state.value += 1 },
    decrement: state => { state.value -= 1 }
  }
});

const store = configureStore({
  reducer: {
    counter: counterSlice.reducer
  }
});

// Component usage
function ReduxCounter() {
  const count = useSelector(state => state.counter.value);
  const dispatch = useDispatch();
  
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => dispatch(counterSlice.actions.increment())}>
        Increment
      </button>
    </div>
  );
}
```

### Zustand Example
```jsx
import create from 'zustand';

const useStore = create(set => ({
  bears: 0,
  increaseBears: () => set(state => ({ bears: state.bears + 1 })),
  removeAllBears: () => set({ bears: 0 })
}));

function BearCounter() {
  const bears = useStore(state => state.bears);
  const increase = useStore(state => state.increaseBears);
  
  return (
    <div>
      <p>Bears: {bears}</p>
      <button onClick={increase}>Add bear</button>
    </div>
  );
}
```

## 4. Server State Management

### React Query Example
```jsx
import { useQuery, useMutation, QueryClient, QueryClientProvider } from 'react-query';

const queryClient = new QueryClient();

function TodoList() {
  const { data: todos, isLoading } = useQuery('todos', fetchTodos);
  const mutation = useMutation(newTodo => {
    return axios.post('/todos', newTodo);
  }, {
    onSuccess: () => {
      queryClient.invalidateQueries('todos');
    }
  });
  
  if (isLoading) return 'Loading...';
  
  return (
    <div>
      {todos.map(todo => (
        <div key={todo.id}>{todo.title}</div>
      ))}
      <button onClick={() => mutation.mutate({ title: 'New Todo' })}>
        Add Todo
      </button>
    </div>
  );
}
```

## 5. Best Practices

### State Location
- Keep state as close as possible to where it's used
- Lift state up only when needed by multiple components
- Use context for truly global state

### State Updates
```jsx
// Bad - Mutating state directly
const [user, setUser] = useState({ name: 'John' });
user.name = 'Jane'; // Wrong!

// Good - Creating new state objects
setUser(prev => ({ ...prev, name: 'Jane' }));

// Good - Updating arrays
const [items, setItems] = useState(['A', 'B']);
setItems(prev => [...prev, 'C']); // Adding
setItems(prev => prev.filter(item => item !== 'B')); // Removing
setItems(prev => prev.map(item => item === 'A' ? 'X' : item)); // Updating
```

### Performance Optimization
```jsx
function MemoizedComponent() {
  // Memoize expensive calculations
  const expensiveValue = useMemo(() => {
    return computeExpensiveValue(a, b);
  }, [a, b]);
  
  // Memoize callbacks
  const handleClick = useCallback(() => {
    doSomething(expensiveValue);
  }, [expensiveValue]);
  
  return <button onClick={handleClick}>Click me</button>;
}
```

Here's a step-by-step guide to creating a React app:

1. Install Node.js from nodejs.org if not already installed

2. Create new app using Create React App:
```bash
npx create-react-app my-app
cd my-app
```

3. Start development server:
```bash
npm start
```

Key files in your new app:
- src/App.js: Main component
- src/index.js: Entry point
- public/index.html: HTML template

Basic component example:
```jsx
function App() {
  return (
    <div>
      <h1>Hello React</h1>
    </div>
  );
}

export default App;
```

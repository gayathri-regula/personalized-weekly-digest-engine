import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState<number>(0)

  return (
    <>
      <h1>Personalized Weekly Digest Engine</h1>
      <div className="card">
        <button onClick={() => setCount((c) => c + 1)}>
          count is {count}
        </button>
        <p>
          Welcome to the Personalized Weekly Digest Engine frontend starter.
        </p>
      </div>
      <p className="read-the-docs">
        Frontend application scaffolded with React + Vite + TypeScript.
      </p>
    </>
  )
}

export default App

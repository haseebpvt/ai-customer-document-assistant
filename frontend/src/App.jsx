import { BrowserRouter, Route, Routes } from 'react-router-dom'
import DocumentPage from './pages/DocumentPage.jsx'
import DocumentsPage from './pages/DocumentsPage.jsx'

export default function App() {
  return (
    <BrowserRouter>
      <main>
        <Routes>
          <Route path="/" element={<DocumentsPage />} />
          <Route path="/documents/:id" element={<DocumentPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}

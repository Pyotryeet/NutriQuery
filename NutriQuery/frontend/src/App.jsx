import React from 'react'
import SearchSection from './components/SearchSection'
import AnalyticsSection from './components/AnalyticsSection'
import MLEngineSection from './components/MLEngineSection'
import BrandsSection from './components/BrandsSection'
import DataImportSection from './components/DataImportSection'

function App() {
  return (
    <div className="app-container">
      <header className="header">
        <div className="logo-container">
          <h1>Nutri<span>Query</span></h1>
          <p className="subtitle">Food and Nutrition Intelligence</p>
        </div>
      </header>

      <main className="main-content">
        <SearchSection />
        <AnalyticsSection />
        <MLEngineSection />
        <BrandsSection />
        <DataImportSection />
      </main>

      <footer style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)', borderTop: '1px solid var(--border-color)', marginTop: '2rem' }}>
        <p>NutriQuery — ISE305 Database Systems Project</p>
      </footer>
    </div>
  )
}

export default App

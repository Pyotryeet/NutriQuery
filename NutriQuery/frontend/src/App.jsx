import React from 'react'
import BrowseSection from './components/BrowseSection'
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
        <BrowseSection />
        <AnalyticsSection />
        <MLEngineSection />
        <BrandsSection />
        <DataImportSection />
      </main>

      <footer className="app-footer">
        <p>NutriQuery — ISE305 Database Systems Project</p>
      </footer>
    </div>
  )
}

export default App

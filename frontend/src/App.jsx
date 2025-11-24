import { DataProvider, useData } from './context/DataContext'
import { FileUpload } from './components/FileUpload'
import { Sidebar } from './components/Sidebar'
import { FitFosterTab } from './components/FitFosterTab'
import { FosterToCauerTab } from './components/FosterToCauerTab'
import { PredictSiblingTab } from './components/PredictSiblingTab'

function AppContent() {
  const { activeTab, setActiveTab, uploadedPoints } = useData()

  const tabs = [
    { id: 'fit', label: 'Fit → Foster', component: FitFosterTab },
    { id: 'cauer', label: 'Foster → Cauer', component: FosterToCauerTab },
    { id: 'predict', label: 'Predict Sibling', component: PredictSiblingTab }
  ]

  const ActiveTabComponent = tabs.find(t => t.id === activeTab)?.component

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-12 gap-6">
          {/* Sidebar */}
          <div className="col-span-3">
            <div className="bg-white rounded-lg shadow p-6 space-y-4">
              <h1 className="text-2xl font-bold text-gray-800">
                Thermal Impedance Toolkit
              </h1>
              
              <FileUpload />
              
              <Sidebar />
              
              {uploadedPoints && (
                <div className="text-xs text-gray-600 bg-green-50 p-2 rounded">
                  ✓ {uploadedPoints.length} data points loaded
                </div>
              )}
            </div>
          </div>

          {/* Main Content */}
          <div className="col-span-9">
            <div className="bg-white rounded-lg shadow p-6">
              {/* Tabs */}
              <div className="flex border-b border-gray-200 mb-6">
                {tabs.map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-6 py-3 font-medium text-sm border-b-2 transition-colors ${
                      activeTab === tab.id
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Active Tab Content */}
              {ActiveTabComponent && <ActiveTabComponent />}
            </div>

            {/* Footer */}
            <div className="mt-4 text-center text-xs text-gray-500">
              Interactive preview (log-log transform applied to plot)
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function App() {
  return (
    <DataProvider>
      <AppContent />
    </DataProvider>
  )
}

export default App

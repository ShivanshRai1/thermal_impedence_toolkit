import { createContext, useState, useContext } from 'react'

const DataContext = createContext()

export function DataProvider({ children }) {
  const [uploadedPoints, setUploadedPoints] = useState(null)
  const [fosterResult, setFosterResult] = useState(null)
  const [cauerResult, setCauerResult] = useState(null)
  const [predictResult, setPredictResult] = useState(null)
  const [activeTab, setActiveTab] = useState('fit')
  const [orderN, setOrderN] = useState(4)
  const [refArea, setRefArea] = useState(1.0)
  const [newArea, setNewArea] = useState('')
  const [gammaMode, setGammaMode] = useState('blended')
  const [gammaFixed, setGammaFixed] = useState(0.8)

  const value = {
    uploadedPoints,
    setUploadedPoints,
    fosterResult,
    setFosterResult,
    cauerResult,
    setCauerResult,
    predictResult,
    setPredictResult,
    activeTab,
    setActiveTab,
    orderN,
    setOrderN,
    refArea,
    setRefArea,
    newArea,
    setNewArea,
    gammaMode,
    setGammaMode,
    gammaFixed,
    setGammaFixed
  }

  return (
    <DataContext.Provider value={value}>
      {children}
    </DataContext.Provider>
  )
}

export function useData() {
  const context = useContext(DataContext)
  if (!context) {
    throw new Error('useData must be used within DataProvider')
  }
  return context
}

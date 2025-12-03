import { useData } from '../context/DataContext'

export function Sidebar() {
  const {
    orderN,
    setOrderN
  } = useData()

  return (
    <div className="bg-white rounded-lg p-4 border border-gray-200">
      <h3 className="font-medium text-gray-800 mb-3">Inputs</h3>
      
      <div className="space-y-3">
        <div>
          <label className="block text-sm text-gray-700 mb-1">
            Order N
          </label>
          <input
            type="number"
            value={orderN}
            onChange={(e) => setOrderN(e.target.value)}
            min="1"
            max="10"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
    </div>
  )
}

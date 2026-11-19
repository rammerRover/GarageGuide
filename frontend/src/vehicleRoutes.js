import { accountRoute } from './accountRoute.js'

export const vehiclesRoute = { id: 'vehicles', path: '/vehicles' }
export const newVehicleRoute = { id: 'new-vehicle', path: '/vehicles/new' }
export const vehicleDetailRoute = { id: 'vehicle-detail', path: '/vehicles/:vehicleId' }
export const serviceHistoryRoute = { id: 'service-history', path: '/vehicles/:vehicleId/services' }
export const serviceRecordRoute = { id: 'service-record', path: '/vehicles/:vehicleId/services/:serviceId' }
export const protectedRoutes = [accountRoute, vehiclesRoute, newVehicleRoute, vehicleDetailRoute, serviceHistoryRoute, serviceRecordRoute]

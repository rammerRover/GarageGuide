import { accountRoute } from './accountRoute.js'

export const vehiclesRoute = { id: 'vehicles', path: '/vehicles' }
export const newVehicleRoute = { id: 'new-vehicle', path: '/vehicles/new' }
export const protectedRoutes = [accountRoute, vehiclesRoute, newVehicleRoute]

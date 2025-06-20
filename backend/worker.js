import { Hono } from 'hono'
import { serveStatic } from 'hono/cloudflare-workers'
import { cors } from 'hono/cors'

const app = new Hono()

// Enable CORS
app.use('/*', cors({
  origin: '*',
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization'],
  exposeHeaders: ['Content-Length', 'X-Kuma-Revision'],
  maxAge: 600,
  credentials: true,
}))

// Serve static assets
app.use('/static/*', serveStatic({ root: './' }))
app.use('/favicon.ico', serveStatic({ root: './' }))
app.use('/logo192.png', serveStatic({ root: './' }))
app.use('/logo512.png', serveStatic({ root: './' }))
app.use('/manifest.json', serveStatic({ root: './' }))
app.use('/robots.txt', serveStatic({ root: './' }))
app.use('/', serveStatic({ root: './', rewriteRequestPath: (path) => '/index.html' }))

// Health check endpoint
app.get('/api', (c) => c.text('Goodwill App API is running'))

// Items endpoint
app.get('/api/items', async (c) => {
  const items = await c.env.GOODWILL_KV.get('items')
  return c.json(JSON.parse(items || '[]'))
})

// Products endpoint (alias for items for frontend compatibility)
app.get('/api/products', async (c) => {
  const items = await c.env.GOODWILL_KV.get('items')
  return c.json(JSON.parse(items || '[]'))
})

// Categories endpoint
app.get('/api/categories', async (c) => {
  const items = await c.env.GOODWILL_KV.get('items')
  const itemsData = JSON.parse(items || '[]')
  const categories = [...new Set(itemsData.map(item => item.search_term).filter(Boolean))]
  return c.json(categories)
})

// Product categories endpoint
app.get('/api/product-categories', async (c) => {
  const items = await c.env.GOODWILL_KV.get('items')
  const itemsData = JSON.parse(items || '[]')
  const categories = [...new Set(itemsData.map(item => item.category_name).filter(Boolean))]
  return c.json(categories)
})

// Locations endpoint
app.get('/api/locations', async (c) => {
  // Return a basic seller map - you may want to store this in KV as well
  const locations = {
    "19": "Portland, OR",
    "198": "Spokane, WA"
  }
  return c.json(locations)
})

// Settings endpoint
app.get('/api/settings', async (c) => {
  const settings = await c.env.GOODWILL_KV.get('settings')
  return c.json(JSON.parse(settings || '[]'))
})

// Favorites endpoint
app.get('/api/favorites', async (c) => {
  const favorites = await c.env.GOODWILL_KV.get('favorites')
  return c.json(JSON.parse(favorites || '[]'))
})

// Promising items endpoint
app.get('/api/promising', async (c) => {
  const promising = await c.env.GOODWILL_KV.get('promising')
  return c.json(JSON.parse(promising || '[]'))
})

// Search endpoint
app.get('/api/search', async (c) => {
  const query = c.req.query('q')
  if (!query) {
    return c.json({ error: 'Query parameter required' }, 400)
  }
  const results = await c.env.GOODWILL_KV.get(`search:${query}`)
  return c.json(JSON.parse(results || '[]'))
})

// Update settings endpoint
app.post('/api/settings', async (c) => {
  const settings = await c.req.json()
  await c.env.GOODWILL_KV.put('settings', JSON.stringify(settings))
  return c.json({ success: true })
})

// Add to favorites endpoint
app.post('/api/favorites', async (c) => {
  const favorite = await c.req.json()
  const favorites = JSON.parse(await c.env.GOODWILL_KV.get('favorites') || '[]')
  favorites.push(favorite.item_id)
  await c.env.GOODWILL_KV.put('favorites', JSON.stringify(favorites))
  return c.json({ status: 'success', message: 'Item added to favorites' })
})

// Remove from favorites endpoint
app.delete('/api/favorites', async (c) => {
  const itemId = c.req.query('item_id')
  if (!itemId) {
    return c.json({ error: 'Item ID is required' }, 400)
  }
  const favorites = JSON.parse(await c.env.GOODWILL_KV.get('favorites') || '[]')
  const updatedFavorites = favorites.filter(id => id !== itemId)
  await c.env.GOODWILL_KV.put('favorites', JSON.stringify(updatedFavorites))
  return c.json({ status: 'success', message: 'Item removed from favorites' })
})

// Add to promising endpoint
app.post('/api/promising', async (c) => {
  const promising = await c.req.json()
  const promisingItems = JSON.parse(await c.env.GOODWILL_KV.get('promising') || '[]')
  promisingItems.push(promising)
  await c.env.GOODWILL_KV.put('promising', JSON.stringify(promisingItems))
  return c.json({ success: true })
})

// Manual search endpoint (placeholder - Workers can't run Python scripts)
app.post('/api/manual-search', async (c) => {
  return c.json({ 
    error: 'Manual search is not available in the Worker deployment. Use the scheduled updates instead.' 
  }, 501)
})

// Manual price update endpoint (placeholder - Workers can't run Python scripts)
app.post('/api/manual-price-update', async (c) => {
  return c.json({ 
    error: 'Manual price update is not available in the Worker deployment. Use the scheduled updates instead.' 
  }, 501)
})

export default {
  fetch: app.fetch
} 
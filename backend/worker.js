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

// Health check endpoint
app.get('/', (c) => c.text('Goodwill App API is running'))

// Items endpoint
app.get('/items', async (c) => {
  const items = await c.env.GOODWILL_KV.get('items')
  return c.json(JSON.parse(items || '[]'))
})

// Settings endpoint
app.get('/settings', async (c) => {
  const settings = await c.env.GOODWILL_KV.get('settings')
  return c.json(JSON.parse(settings || '[]'))
})

// Favorites endpoint
app.get('/favorites', async (c) => {
  const favorites = await c.env.GOODWILL_KV.get('favorites')
  return c.json(JSON.parse(favorites || '[]'))
})

// Promising items endpoint
app.get('/promising', async (c) => {
  const promising = await c.env.GOODWILL_KV.get('promising')
  return c.json(JSON.parse(promising || '[]'))
})

// Search endpoint
app.get('/search', async (c) => {
  const query = c.req.query('q')
  if (!query) {
    return c.json({ error: 'Query parameter required' }, 400)
  }
  const results = await c.env.GOODWILL_KV.get(`search:${query}`)
  return c.json(JSON.parse(results || '[]'))
})

// Update settings endpoint
app.post('/settings', async (c) => {
  const settings = await c.req.json()
  await c.env.GOODWILL_KV.put('settings', JSON.stringify(settings))
  return c.json({ success: true })
})

// Add to favorites endpoint
app.post('/favorites', async (c) => {
  const favorite = await c.req.json()
  const favorites = JSON.parse(await c.env.GOODWILL_KV.get('favorites') || '[]')
  favorites.push(favorite)
  await c.env.GOODWILL_KV.put('favorites', JSON.stringify(favorites))
  return c.json({ success: true })
})

// Add to promising endpoint
app.post('/promising', async (c) => {
  const promising = await c.req.json()
  const promisingItems = JSON.parse(await c.env.GOODWILL_KV.get('promising') || '[]')
  promisingItems.push(promising)
  await c.env.GOODWILL_KV.put('promising', JSON.stringify(promisingItems))
  return c.json({ success: true })
})

export default {
  fetch: app.fetch
} 
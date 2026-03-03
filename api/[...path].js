const EC2_BACKEND = process.env.EC2_BACKEND_URL || 'http://18.60.156.119:8081';

export default async function handler(req, res) {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    return res.status(200).end();
  }

  const path = req.url; // e.g. /api/health, /api/token?room=gram-sahayak
  const targetUrl = `${EC2_BACKEND}${path}`;

  try {
    const backendRes = await fetch(targetUrl, {
      method: req.method,
      headers: { 'Content-Type': 'application/json' },
    });

    const body = await backendRes.text();

    res.setHeader('Content-Type', 'application/json');
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.status(backendRes.status).send(body);
  } catch (err) {
    res.setHeader('Content-Type', 'application/json');
    res.status(502).json({
      error: 'Backend unavailable',
      target: targetUrl,
      details: err.message,
    });
  }
}

export const config = {
  runtime: 'edge',
};

const EC2_BACKEND = process.env.EC2_BACKEND_URL || 'http://18.60.156.119:8081';

export default async function handler(request) {
  const url = new URL(request.url);
  const path = url.pathname.replace(/^\/api/, '/api');
  const search = url.search;
  const targetUrl = `${EC2_BACKEND}${path}${search}`;

  try {
    const backendRes = await fetch(targetUrl, {
      method: request.method,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const body = await backendRes.text();

    return new Response(body, {
      status: backendRes.status,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({ error: 'Backend unavailable', details: err.message }),
      {
        status: 502,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}

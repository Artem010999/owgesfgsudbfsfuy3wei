const http = require("http");
const PORT = process.env.PORT || 4000;

function sendJson(res, status, data) {
  const body = JSON.stringify(data);
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
  });
  res.end(body);
}

const server = http.createServer((req, res) => {
  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
    });
    return res.end();
  }

  if (req.url === "/api/chat" && req.method === "POST") {
    let chunked = '';
    req.on("data", c => chunked += c);
    req.on("end", () => {
      try {
        const parsed = chunked ? JSON.parse(chunked) : {};
        const msg = (parsed && parsed.message) ? String(parsed.message) : '';
        const reply = `Вайб принят: «${msg.slice(0, 140)}». Собираем рабочее настроение.`;
        // Simulate small delay
        setTimeout(() => sendJson(res, 200, { reply }), 400);
      } catch (e) {
        return sendJson(res, 400, { error: "Bad JSON" });
      }
    });
    return;
  }

  res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
  res.end("Not found");
});

server.listen(PORT, () => {
  console.log(`API listening on http://127.0.0.1:${PORT}`);
});






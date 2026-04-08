/* 
  Proxy function to fetch trade history from the VPS 
*/
export default async function handler(req, res) {
  const VPS_IP = "3.6.147.81";
  const VPS_PORT = "8050";
  
  try {
    const response = await fetch(`http://${VPS_IP}:${VPS_PORT}/api/trades`);
    const data = await response.json();
    res.status(200).json(data);
  } catch (error) {
    console.error("VPS Fetch Error (Trades):", error);
    res.status(500).json({ error: "Failed to connect to VPS API" });
  }
}

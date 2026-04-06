import { useEffect, useState, type SetStateAction } from "react";
import { api } from "./api/client";

function App() {
  const [status, setStatus] = useState("checking...");

  useEffect(() => {
    api.get("/health")
      .then((res: { data: { status: SetStateAction<string>; }; }) => setStatus(res.data.status))
      .catch(() => setStatus("error"));
  }, []);

  return (
    <div style={{ padding: 24, fontFamily: "sans-serif" }}>
      <h1>GroundedIQ</h1>
      <p>API status: {status}</p>
    </div>
  );
}

export default App;
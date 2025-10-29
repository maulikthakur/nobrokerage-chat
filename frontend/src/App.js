import React, { useState } from "react";

function App() {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState(null);

  const handleSend = async () => {
    const res = await fetch("http://127.0.0.1:5000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await res.json();
    setResponse(data);
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "Arial" }}>
      <h1>🏠 NoBrokerage Chat</h1>
      <div>
        <input
          style={{ width: "300px", padding: "8px" }}
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask e.g., 3BHK in Pune under 1.2 Cr"
        />
        <button onClick={handleSend} style={{ marginLeft: "10px", padding: "8px" }}>
          Send
        </button>
      </div>

      {response && (
        <div style={{ marginTop: "2rem" }}>
          <h3>Bot Response:</h3>
          <p>{response.message}</p>
          {response.results?.map((r, i) => (
            <div key={i} style={{ border: "1px solid #ccc", padding: "10px", marginTop: "10px" }}>
              <h4>{r.projectName}</h4>
              <p>BHK: {r.bhk}</p>
              <p>City: {r.city}</p>
              <p>Price: {r.price}</p>
              <p>Status: {r.status}</p>
              <p>Amenities: {r.amenities}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;

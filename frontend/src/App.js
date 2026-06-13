import { useEffect, useState } from "react";
import axios from "axios";

function App() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    axios.get("http://127.0.0.1:8000/events")
      .then(res => setEvents(res.data))
      .catch(err => console.log(err));
  }, []);

  return (
    <div style={{ padding: "20px" }}>
      <h1>College Events</h1>

      {events.length === 0 ? (
        <p>No events found</p>
      ) : (
        events.map((event, index) => (
          <div key={index} style={{
            border: "1px solid black",
            margin: "10px",
            padding: "10px"
          }}>
            <h3>{event.name}</h3>
            <p>{event.date}</p>
            <p>{event.location}</p>
          </div>
        ))
      )}
    </div>
  );
}

export default App;
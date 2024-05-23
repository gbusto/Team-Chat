import React, { useState, useEffect, useRef } from 'react';
import { w3cwebsocket as W3CWebSocket } from 'websocket';
import './App.css';

let client;

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [id, setId] = useState('');
  const [name, setName] = useState('');
  const messageEndRef = useRef(null);

  const connectWebSocket = () => {
    client = new W3CWebSocket('ws://localhost:9999');

    client.onopen = () => {
      console.log('WebSocket Client Connected');
      setIsConnected(true);

      const connectMsg = {
        type: 'cli_connect',
        name: name,
        id: id,
        being: 'human',
        host: 'localhost',
        port: 3000
      };
      client.send(JSON.stringify(connectMsg));
      console.log('Connected as:', connectMsg);
    };

    client.onmessage = (message) => {
      const dataFromServer = JSON.parse(message.data);
      console.log('Received:', dataFromServer);
      if (dataFromServer.type === 'msg_recvd') {
        setMessages((prevMessages) => [...prevMessages, dataFromServer]);
      }
    };

    client.onclose = () => {
      console.log('WebSocket Client Disconnected');
      setIsConnected(false);
      // Try to reconnect
      setTimeout(connectWebSocket, 5000); // 5 seconds retry interval
    };

    client.onerror = (error) => {
      console.error('WebSocket Error:', error);
    };
  };

  const sendMessage = () => {
    if (input && isConnected) {
      const message = {
        type: 'msg_recvd',
        from: id, // Use dynamic user identification
        origin: 'human',
        message: input,
        timestamp: new Date().toISOString() // Add timestamp
      };
      console.log('Sending:', message);
      client.send(JSON.stringify(message));
      setMessages((prevMessages) => [...prevMessages, message]); // Add the message to the state
      setInput('');
    }
  };

  const scrollToBottom = () => {
    messageEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  const renderMessage = (msg, index) => {
    const className = msg.origin;
    const sender = msg.from.startsWith("[") ? msg.from.match(/\[(.*?)\]/)[1] : msg.from;
    const messageText = msg.from.startsWith("[") ? msg.message.replace(`[${sender}] `, "") : msg.message;
    const timestamp = new Date(msg.timestamp).toLocaleString('en-US', {
      month: 'short',
      day: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });

    return (
      <div key={index} className="message">
        <span className={`sender ${className}`}>
          {sender} <span className="timestamp">@ {timestamp}</span>
        </span>
        <span className="text">{messageText}</span>
      </div>
    );
  };

  return (
    <div className="App">
      {!isConnected ? (
        <div className="login-container">
          <input
            type="text"
            placeholder="ID"
            value={id}
            onChange={(e) => setId(e.target.value)}
          />
          <input
            type="text"
            placeholder="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <button onClick={connectWebSocket} disabled={!id || !name}>
            Connect
          </button>
        </div>
      ) : (
        <div className="chat-container">
          <div className="messages">
            {messages.map(renderMessage)}
            <div ref={messageEndRef} />
          </div>
          <div className="input-container">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
            />
            <button onClick={sendMessage} disabled={!isConnected}>Send</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;

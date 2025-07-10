import { useState } from "react";
import { Phone, PhoneOff, Activity } from "lucide-react";
import { RoomEvent } from "livekit-client";
import {
  LiveKitRoom,
  useRoomContext,
  useTracks,
} from "@livekit/components-react";
import { Track } from "livekit-client";
import "./App.css";

interface CallData {
  call_id: string;
  room_name: string;
  status: string;
  message: string;
}

interface TokenData {
  token: string;
  url: string;
}

function VoiceInterface() {
  const room = useRoomContext();
  const tracks = useTracks([Track.Source.Microphone], {
    onlySubscribed: false,
  });
  const [isConnected, setIsConnected] = useState(false);

  // Monitor connection state
  room.on(RoomEvent.Connected, () => {
    console.log("Connected to room");
    setIsConnected(true);
  });

  room.on(RoomEvent.Disconnected, () => {
    console.log("Disconnected from room");
    setIsConnected(false);
  });

  return (
    <div className="space-y-4">
      <div
        className={`text-center p-3 rounded-lg ${
          isConnected
            ? "bg-green-100 text-green-800"
            : "bg-orange-100 text-orange-800"
        }`}
      >
        {isConnected
          ? "🎤 Connected - You can speak with the agent"
          : "⏳ Connecting to voice room..."}
      </div>

      {tracks.length > 0 && (
        <div className="text-sm text-gray-600 text-center">
          <p>
            Microphone tracks:{" "}
            {tracks.filter((t) => t.source === Track.Source.Microphone).length}
          </p>
          <p>
            Agent tracks:{" "}
            {
              tracks.filter(
                (t) => t.publication.kind === "audio" && !t.publication.isLocal
              ).length
            }
          </p>
        </div>
      )}
    </div>
  );
}

function App() {
  const [currentCall, setCurrentCall] = useState<CallData | null>(null);
  const [tokenData, setTokenData] = useState<TokenData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState("Ready to create calls");

  const startCall = async () => {
    try {
      setIsLoading(true);
      setStatus("Creating call...");

      // 1. Create the call
      const callResponse = await fetch("http://localhost:8000/calls/start", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({}),
      });

      if (!callResponse.ok) {
        throw new Error(`HTTP error! status: ${callResponse.status}`);
      }

      const callData = await callResponse.json();
      setCurrentCall(callData);

      // 2. Get access token for the room
      setStatus("Getting access token...");
      const tokenResponse = await fetch("http://localhost:8000/token", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          room_name: callData.room_name,
          participant_name: "Patient",
        }),
      });

      if (!tokenResponse.ok) {
        throw new Error(`Token error! status: ${tokenResponse.status}`);
      }

      const tokenData = await tokenResponse.json();
      setTokenData(tokenData);
      setStatus(
        `Connecting to voice room: ${callData.call_id.substring(0, 8)}`
      );
    } catch (error) {
      console.error("Error starting call:", error);
      setStatus("Failed to start call");
      setCurrentCall(null);
      setTokenData(null);
    } finally {
      setIsLoading(false);
    }
  };

  const endCall = async () => {
    if (!currentCall) return;

    try {
      setIsLoading(true);
      setStatus("Ending call...");

      const response = await fetch(
        `http://localhost:8000/calls/${currentCall.call_id}/end`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setCurrentCall(null);
      setTokenData(null);
      setStatus("Call ended");

      // Reset to ready state after 2 seconds
      setTimeout(() => {
        setStatus("Ready to create calls");
      }, 2000);
    } catch (error) {
      console.error("Error ending call:", error);
      setStatus("Failed to end call");
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = () => {
    if (status.includes("Failed")) return "text-red-600 bg-red-50";
    if (status.includes("Connecting") || status.includes("Connected"))
      return "text-green-700 bg-green-50";
    if (status.includes("ended")) return "text-orange-700 bg-orange-50";
    if (
      status.includes("Creating") ||
      status.includes("Ending") ||
      status.includes("Getting")
    )
      return "text-blue-700 bg-blue-50";
    return "text-gray-700 bg-gray-50";
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-6 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <Activity className="w-8 h-8 text-indigo-600 mr-3" />
            <h1 className="text-4xl font-bold text-gray-900">
              Medical Triage Voice AI
            </h1>
          </div>
          <p className="text-xl text-gray-600">
            Speak with our medical triage agent
          </p>
        </div>

        {/* Main Interface */}
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-2xl shadow-xl p-8">
            {/* Status */}
            <div
              className={`text-center p-4 rounded-xl mb-8 font-medium ${getStatusColor()}`}
            >
              {status}
            </div>

            {/* Voice Room Connection */}
            {tokenData && currentCall && (
              <div className="mb-8">
                <LiveKitRoom
                  token={tokenData.token}
                  serverUrl={tokenData.url}
                  connect={true}
                  audio={true}
                  video={false}
                  onConnected={() => {
                    console.log("LiveKit room connected");
                    setStatus(`🎤 Connected to medical triage - Speak now!`);
                  }}
                  onDisconnected={() => {
                    console.log("LiveKit room disconnected");
                  }}
                  onError={(error) => {
                    console.error("LiveKit error:", error);
                    setStatus("Connection error - please try again");
                  }}
                >
                  <VoiceInterface />
                </LiveKitRoom>
              </div>
            )}

            {/* Controls */}
            <div className="flex gap-4 justify-center mb-8">
              <button
                onClick={startCall}
                disabled={isLoading || !!currentCall}
                className="flex items-center gap-3 px-8 py-4 bg-green-600 text-white font-semibold rounded-xl 
                         hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed 
                         transition-all duration-200 transform hover:scale-105 disabled:hover:scale-100"
              >
                <Phone className="w-5 h-5" />
                Start Call
              </button>

              <button
                onClick={endCall}
                disabled={isLoading || !currentCall}
                className="flex items-center gap-3 px-8 py-4 bg-red-600 text-white font-semibold rounded-xl 
                         hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed 
                         transition-all duration-200 transform hover:scale-105 disabled:hover:scale-100"
              >
                <PhoneOff className="w-5 h-5" />
                End Call
              </button>
            </div>

            {/* Call Info */}
            {currentCall && (
              <div className="bg-gray-50 rounded-xl p-6 space-y-3">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Active Voice Call
                </h3>
                <div className="space-y-2 font-mono text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Call ID:</span>
                    <span className="text-gray-900">{currentCall.call_id}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Room:</span>
                    <span className="text-gray-900">
                      {currentCall.room_name}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Status:</span>
                    <span className="text-gray-900 capitalize">
                      {currentCall.status}
                    </span>
                  </div>
                </div>

                {tokenData && (
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>Instructions:</strong> The medical triage agent
                      will greet you and ask about your symptoms. Speak clearly
                      and the agent will route you to the appropriate
                      department.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex items-center justify-center mt-6">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
              </div>
            )}
          </div>

          {/* API Info */}
          <div className="mt-8 text-center text-gray-600">
            <p className="text-sm">
              Medical Triage Voice AI - Powered by LiveKit Agents
            </p>
            <p className="text-xs mt-2">
              Backend:{" "}
              <code className="bg-gray-200 px-2 py-1 rounded">
                http://localhost:8000
              </code>{" "}
              | Frontend:{" "}
              <code className="bg-gray-200 px-2 py-1 rounded">
                http://localhost:7000
              </code>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;

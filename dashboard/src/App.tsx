import React from "react";
import { Routes, Route, Link } from "react-router-dom";
import NotFound from "./pages/NotFound";
import Login from "./pages/Login";
import Signup from "./pages/Signup";

export default function App() {
    return (
        <div style={{ padding: 16 }}>
            {/* <nav style={{ display: "flex", gap: 12, marginBottom: 16 }}>
                <Link to="/">Home</Link>
                <Link to="/about">About</Link>
            </nav> */}

            <Routes>
                <Route path="*" element={<NotFound />} />
                <Route path="/login" element={<Login />} />
                <Route path="/signup" element={<Signup />} />
            </Routes>
        </div>
    );
}

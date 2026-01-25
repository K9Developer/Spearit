import React from "react";
import { Routes, Route, Link } from "react-router-dom";
import NotFound from "./pages/NotFound";
import Login from "./pages/Login";

export default function App() {
    return (
        <div>
            {/* <nav style={{ display: "flex", gap: 12, marginBottom: 16 }}>
                <Link to="/">Home</Link>
                <Link to="/about">About</Link>
            </nav> */}

            <Routes>
                <Route path="*" element={<NotFound />} />
                <Route path="/login" element={<Login />} />
            </Routes>
        </div>
    );
}

import { Routes, Route } from "react-router-dom";
import { Dashboard } from "./features/dashboard/Dashboard";
import { Workspace } from "./features/workspace/Workspace";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/investigations/:id" element={<Workspace />} />
    </Routes>
  );
}

export default App;

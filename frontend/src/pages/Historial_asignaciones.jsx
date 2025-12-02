import { useEffect, useState } from "react";
import Swal from "sweetalert2";
import { API_URL } from "../config";
import "./Unidades.css";

export default function HistorialAsignaciones() {
  const [historial, setHistorial] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const itemsPerPageOptions = [5, 10, 20, 50, "Todos"];

  // Fetch historial desde el endpoint que devuelve nombres
  const fetchHistorial = async () => {
    try {
      const res = await fetch(`${API_URL}/historial_asignaciones`);
      const data = await res.json();
      // Filtrar solo los que tienen fecha_fin
      const filtrado = data.filter(h => h.fecha_fin);
      setHistorial(filtrado);
    } catch (err) {
      console.error(err);
      Swal.fire("Error", "No se pudo cargar el historial", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistorial();
  }, []);

  if (loading) return <p>Cargando historial...</p>;

  // Paginación
  const totalPages = Math.ceil(historial.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentData = historial.slice(startIndex, startIndex + itemsPerPage);

  return (
    <div className="unidades-container" style={{ padding: 10 }}>
      <h2>Historial de Asignaciones</h2>

      {/* Selector de items por página */}
      <div
        className="pagination-controls"
        style={{
          marginBottom: 10,
          display: "flex",
          gap: 10,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <label style={{ fontSize: "0.9rem" }}>
          Mostrar:
          <select
            value={itemsPerPage}
            onChange={e => {
              const val = e.target.value === "Todos" ? historial.length : Number(e.target.value);
              setItemsPerPage(val);
              setCurrentPage(1); // reinicia a página 1 al cambiar el tamaño
            }}
          >
            {itemsPerPageOptions.map(opt => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </label>
      </div>

      {/* Tabla */}
      <div style={{ overflowX: "auto" }}>
        <table className="elegant-table" style={{ width: "100%", minWidth: 700 }}>
          <thead>
            <tr>
              <th>ID Historial</th>
              <th>Unidad</th>
              <th>Chofer</th>
              <th>Fecha Asignación</th>
              <th>Fecha Fin</th>
              <th>Usuario</th>
              <th>Fecha Cambio</th>
            </tr>
          </thead>
          <tbody>
            {currentData.length > 0 ? (
              currentData.map(h => (
                <tr key={h.id_historial}>
                  <td>{h.id_historial}</td>
                  <td>{h.id_unidad} - {h.nombre_unidad}</td>
                <td>{h.nombre_chofer}</td>

                  <td>
                    {h.fecha_asignacion ? new Date(h.fecha_asignacion).toLocaleDateString("es-MX") : "-"}
                  </td>
                  <td>{h.fecha_fin ? new Date(h.fecha_fin).toLocaleDateString("es-MX") : "-"}</td>
                  <td>{h.usuario}</td>
                  <td>{h.fecha_cambio ? new Date(h.fecha_cambio).toLocaleString("es-MX") : "-"}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="7" style={{ textAlign: "center" }}>
                  No hay historial con fecha de fin
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      <div
        className="pagination"
        style={{
          marginTop: 10,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: 10,
          flexWrap: "wrap",
        }}
      >
        <button onClick={() => setCurrentPage(p => Math.max(p - 1, 1))} disabled={currentPage === 1}>
          <i className="fa-solid fa-arrow-left"></i>
        </button>
        <span>
          Página {currentPage} de {totalPages}
        </span>
        <button
          onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))}
          disabled={currentPage === totalPages}
        >
          <i className="fa-solid fa-arrow-right"></i>
        </button>
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { API_URL } from "../config";
import ModalFile from "../components/ModalFile";

export default function HistorialPlacas() {
  const [historial, setHistorial] = useState([]);
  const [fileModalUrl, setFileModalUrl] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [search, setSearch] = useState("");

  useEffect(() => {
    fetchHistorial();
  }, []);

  const fetchHistorial = async () => {
    try {
      const res = await fetch(`${API_URL}/placas/historial`);
      const data = await res.json();
      setHistorial(data.historial || []);
    } catch (err) {
      console.error(err);
      alert("No se pudo cargar el historial");
    }
  };

  // Filtrado por búsqueda
  const filteredHistorial = historial.filter(h => 
    (h.placa || "").toLowerCase().includes(search.toLowerCase()) ||
    (h.nombre_unidad || "").toLowerCase().includes(search.toLowerCase())
  );

  // Paginación
  let currentItems = filteredHistorial;
  let totalPages = 1;

  if (itemsPerPage !== "Todos") {
    const perPage = Number(itemsPerPage);
    const indexOfLastItem = currentPage * perPage;
    const indexOfFirstItem = indexOfLastItem - perPage;
    currentItems = filteredHistorial.slice(indexOfFirstItem, indexOfLastItem);
    totalPages = Math.ceil(filteredHistorial.length / perPage);
  }

  return (
    <div className="historial-container">
      <h1>Historial de Placas</h1>

      {/* Filtro */}
      <div style={{ marginBottom: "1rem" }}>
        <input
          type="text"
          placeholder="Buscar por placa o unidad..."
          value={search}
          onChange={e => { setSearch(e.target.value); setCurrentPage(1); }}
        />
        <select value={itemsPerPage} onChange={e => setItemsPerPage(e.target.value)}>
          <option value={5}>5</option>
          <option value={10}>10</option>
          <option value={25}>25</option>
          <option value={50}>50</option>
          <option value="Todos">Todos</option>
        </select>
      </div>

      <div className="table-wrapper">
        <table className="elegant-table">
<thead>
  <tr>
    <th>ID Unidad</th>
    <th>Placa</th>
    <th>Unidad</th>
    <th>Folio</th>
    <th>Expedición</th>
    <th>Vigencia</th>
    <th>Monto Pago</th>
    <th>Frontal</th>
    <th>Trasera</th>
    <th>Comprobante</th>
    <th>Tarjeta Circulación</th>
    <th>Usuario</th>
  </tr>
</thead>
<tbody>
  {currentItems.map(h => (
    <tr key={h.id_unidad}>
      <td>{h.id_unidad}</td>
      <td>{h.placa || "N/A"}</td>
      <td>{h.nombre_unidad || "N/A"} - {h.modelo || "N/A"}</td>
      <td>{h.folio || "N/A"}</td>
      <td>{h.fecha_expedicion || "N/A"}</td>
      <td>{h.fecha_vigencia || "N/A"}</td>
      <td>{h.monto_pago ? `$${h.monto_pago}` : "N/A"}</td>
      <td>
        {h.url_placa_frontal ? (
          <button className="btn btn-outline-danger btn-sm" onClick={() => setFileModalUrl(`${API_URL}/${h.url_placa_frontal}`)}>Ver</button>
        ) : "N/A"}
      </td>
      <td>
        {h.url_placa_trasera ? (
          <button className="btn btn-outline-danger btn-sm" onClick={() => setFileModalUrl(`${API_URL}/${h.url_placa_trasera}`)}>Ver</button>
        ) : "N/A"}
      </td>
      <td>
        {h.url_comprobante_pago ? (
          <button className="btn btn-outline-danger btn-sm" onClick={() => setFileModalUrl(`${API_URL}/${h.url_comprobante_pago}`)}>Ver</button>
        ) : "N/A"}
      </td>
      <td>
        {h.url_tarjeta_circulacion ? (
          <button className="btn btn-outline-danger btn-sm" onClick={() => setFileModalUrl(`${API_URL}/${h.url_tarjeta_circulacion}`)}>Ver</button>
        ) : "N/A"}
      </td>
      <td>{h.usuario || "N/A"}</td>
    </tr>
  ))}
</tbody>

        </table>
      </div>

      {/* Paginación */}
      <div className="pagination">
        {itemsPerPage !== "Todos" && (
          <>
            <button 
              disabled={currentPage === 1} 
              onClick={() => setCurrentPage(prev => prev - 1)}
            >
              Anterior
            </button>
            <span>Página {currentPage} de {totalPages}</span>
            <button 
              disabled={currentPage === totalPages} 
              onClick={() => setCurrentPage(prev => prev + 1)}
            >
              Siguiente
            </button>
          </>
        )}
        
      </div>

      {fileModalUrl && <ModalFile url={fileModalUrl} onClose={() => setFileModalUrl(null)} />}
    </div>
  );
}

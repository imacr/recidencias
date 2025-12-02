import { useEffect, useState } from "react";
import { API_URL } from "../config";
import ModalFile from "../components/ModalFile";

export default function HistorialGarantias() {
  const [historiales, setHistoriales] = useState([]);
  const [modalUrl, setModalUrl] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/api/historial_garantias`)
      .then((res) => {
        if (!res.ok) throw new Error("Error en la respuesta del servidor");
        return res.json();
      })
      .then((data) => setHistoriales(data))
      .catch((err) => console.error("Error cargando historial de pólizas:", err));
  }, []);

  const abrirModal = (url) => setModalUrl(`${API_URL}/${url}`);
  const cerrarModal = () => setModalUrl(null);

  return (
    <div className="unidades-container">
      <h1>Historial de Pólizas de Garantía</h1>

      <div className="table-wrapper">
        <table className="elegant-table">
          <thead>
            <tr>
              <th style={{ display: "none" }}>ID</th>
              <th>ID Unidad</th>
              <th>ID Garantía</th>
              <th>Aseguradora</th>
              <th>Tipo Garantía</th>
              <th>No. Póliza</th>
              <th>Suma Asegurada</th>
              <th>Inicio Vigencia</th>
              <th>Vigencia</th>
              <th>Prima</th>
              <th>Archivo</th>
              <th>Usuario</th>
              <th>Fecha de Cambio</th>
            </tr>
          </thead>

          <tbody>
            {historiales.length > 0 ? (
              historiales.map((h, i) => (
                <tr key={i}>
                  <td style={{ display: "none" }}>{h.id}</td>
                  <td>{h.id_unidad}</td>
                  <td>{h.id_garantia}</td>
                  <td>{h.aseguradora}</td>
                  <td>{h.tipo_garantia}</td>
                  <td>{h.no_poliza}</td>
                  <td>${h.suma_asegurada?.toLocaleString("es-MX", { minimumFractionDigits: 2 })}</td>
                  <td>{h.inicio_vigencia || "-"}</td>
                  <td>{h.vigencia || "-"}</td>
                  <td>${h.prima?.toLocaleString("es-MX", { minimumFractionDigits: 2 })}</td>
                  <td>
                    {h.url_poliza ? (
                      <button
                        onClick={() => abrirModal(h.url_poliza)}
                        className="btn btn-outline-danger btn-sm"
                        title="Ver PDF de póliza"
                      >
                        Ver PDF
                      </button>
                    ) : (
                      "-"
                    )}
                  </td>
                  <td>{h.usuario}</td>
                  <td>{h.fecha_cambio}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="13" style={{ textAlign: "center" }}>
                  No hay registros disponibles
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {modalUrl && <ModalFile url={modalUrl} onClose={cerrarModal} />}
    </div>
  );
}

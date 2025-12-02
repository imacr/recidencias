import { useEffect, useState } from "react";
import { API_URL } from "../config";
import ModalFile from "../components/ModalFile";

export default function HistorialMantenimientos() {
  const [mantenimientos, setMantenimientos] = useState([]);
  const [modalUrl, setModalUrl] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/mantenimientos`)
      .then((res) => {
        if (!res.ok) throw new Error("Error en servidor");
        return res.json();
      })
      .then((data) => setMantenimientos(data))
      .catch((err) => console.error("Error cargando mantenimientos:", err));
  }, []);

  const abrirModal = (url) => setModalUrl(`${API_URL}/${url}`);
  const cerrarModal = () => setModalUrl(null);

  return (
    <div className="unidades-container">
      <h1>Historial de Mantenimientos</h1>

      <div className="table-wrapper">
        <table className="elegant-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>ID Unidad</th>
              <th>Tipo de Mantenimiento</th>
              <th>Descripción</th>
              <th>Fecha Realización</th>
              <th>Kilometraje</th>
              <th>Realizado Por</th>
              <th>Empresa Garantía</th>
              <th>Cobertura Garantía</th>
              <th>Costo</th>
              <th>Observaciones</th>
              <th>Comprobante</th>
            </tr>
          </thead>

          <tbody>
            {mantenimientos.map((m, i) => (
              <tr key={i}>
                <td>{m.id_mantenimiento}</td>
                <td>{m.id_unidad}</td>
                <td>{m.tipo_mantenimiento}</td>
                <td>{m.descripcion || "-"}</td>
                <td>{m.fecha_realizacion}</td>
                <td>{m.kilometraje}</td>
                <td>{m.realizado_por || "-"}</td>
                <td>{m.empresa_garantia || "-"}</td>
                <td>{m.cobertura_garantia || "-"}</td>
                <td>{m.costo || "-"}</td>
                <td>{m.observaciones || "-"}</td>

                <td>
                  {m.url_comprobante ? (
                    <button
                      onClick={() => abrirModal(m.url_comprobante)}
                      className="btn btn-outline-danger btn-sm"
                      title="Ver comprobante"
                    >
                      Abrir PDF
                    </button>
                  ) : (
                    "-"
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modalUrl && <ModalFile url={modalUrl} onClose={cerrarModal} />}
    </div>
  );
}

import { useEffect, useState } from "react";
import { API_URL } from "../config";
import ModalFile from "../components/ModalFile";

export default function Historiales() {
  const [historiales, setHistoriales] = useState([]);
  const [modalUrl, setModalUrl] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/historiales`)
      .then((res) => {
        if (!res.ok) throw new Error("Error en la respuesta del servidor");
        return res.json();
      })
      .then((data) => setHistoriales(data))
      .catch((err) => console.error("Error cargando historiales:", err));
  }, []);

  const abrirModal = (url) => setModalUrl(`${API_URL}/${url}`);
  const cerrarModal = () => setModalUrl(null);

  return (
    <div className="unidades-container">
      <h1>Historial de Refrendo y Tenencia</h1>

      <div className="table-wrapper">
        <table className="elegant-table">
          <thead>
            <tr>
              <th style={{ display: "none" }}>ID</th>
              <th>ID Unidad</th>
              <th>Vehículo</th>
              <th>Tipo de Pago</th>
              <th>Monto</th>
              <th>Monto Refrendo</th>
              <th>Monto Tenencia</th>
              <th>Fecha de Pago</th>
              <th>Factura</th>{/* <-- Solo una */}
              <th>Observaciones</th>
              <th>Tipo Movimiento</th>
              <th>Usuario</th>
              <th>Fecha Registro</th>
            </tr>
          </thead>

          <tbody>
            {historiales.map((h, i) => (
              <tr key={i}>
                <td style={{ display: "none" }}>{h.id_historial}</td>
                <td>{h.id_unidad}</td>
                <td>{h.vehiculo_modelo}</td>
                <td>{h.tipo_pago}</td>
                <td>{h.monto}</td>
                <td>{h.monto_refrendo}</td>
                <td>{h.monto_tenencia}</td>
                <td>{h.fecha_pago}</td>

                {/* -------------------------- */}
                {/* Solo un archivo para mostrar */}
                {/* -------------------------- */}
                <td>
                  {h.url_factura ? (
                    <button
                      onClick={() => abrirModal(h.url_factura)}
                      className="btn btn-outline-danger btn-sm"
                      title="Ver factura"
                    >
                      Abrir PDF
                    </button>
                  ) : (
                    "-"
                  )}
                </td>

                <td>{h.observaciones}</td>
                <td>{h.tipo_movimiento}</td>
                <td>{h.usuario_registro}</td>
                <td>{h.fecha_registro}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {modalUrl && <ModalFile url={modalUrl} onClose={cerrarModal} />}
    </div>
  );
}
